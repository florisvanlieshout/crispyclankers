"""Real-browser checks of the actual site. Never send a live lead.

Run directly after installing Playwright + Chromium/WebKit. No production mocks:
only blocked autoplay and media-network failure scenarios stub browser boundaries.
"""
import functools
import http.server
import json
import tempfile
import threading
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[1]


class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


def run():
    server = http.server.ThreadingHTTPServer(
        ('127.0.0.1', 0), functools.partial(QuietHandler, directory=str(ROOT)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    base = 'http://127.0.0.1:' + str(server.server_port)
    screenshots = Path(tempfile.mkdtemp(prefix='crispy-hero-'))
    results = []
    try:
        with sync_playwright() as p:
            for engine in ['chromium', 'webkit']:
                browser = getattr(p, engine).launch()
                external = []
                errors = []

                def page_for(**options):
                    context = browser.new_context(**options)
                    def local_only(route):
                        url = route.request.url
                        local_blob = url.startswith('blob:' + base + '/')
                        if urlparse(url).hostname != '127.0.0.1' and not local_blob:
                            external.append(route.request.url)
                            route.abort()
                        else:
                            route.continue_()
                    context.route('**/*', local_only)
                    page = context.new_page()
                    page.on('pageerror', lambda error: errors.append(str(error)))
                    return context, page

                def cta_visible(page):
                    page.locator('.hero-call').wait_for(state='visible')
                    assert page.locator('video').count() == 0
                    assert page.locator('.hero-media').get_attribute('data-state') == 'cta'

                # Two real media decodes: desktop Dutch at normal speed (45 sec),
                # mobile English at 4x (same ended events, no synthetic dispatch).
                for path, width, speed, label in [('/nl/', 1280, 1, 'Clanky, bel mij nu!'),
                                                  ('/', 390, 4, 'Clanky, call me now!')]:
                    context, page = page_for(viewport={'width': width, 'height': 900})
                    page.goto(base + path)
                    page.wait_for_function("document.querySelector('video').currentTime > 0.1")
                    assert page.locator('video').evaluate('(v) => v.muted && v.playsInline && !v.loop')
                    before = page.locator('.hero-media').bounding_box()
                    assert before['y'] + before['height'] <= 900, before
                    assert page.evaluate('document.documentElement.scrollWidth <= innerWidth')
                    assert not page.locator('.hero-call').is_visible()
                    page.screenshot(path=str(screenshots / f'{engine}-{width}-playing.png'))
                    page.locator('video').evaluate('(v, rate) => v.playbackRate = rate', speed)
                    page.wait_for_function("document.querySelector('.hero-media').dataset.completedPlays === '1'", timeout=25000)
                    assert not page.locator('.hero-call').is_visible()
                    page.wait_for_function("document.querySelector('.hero-media').dataset.completedPlays === '2'", timeout=25000)
                    assert not page.locator('.hero-call').is_visible()
                    page.wait_for_function("document.querySelector('.hero-media').dataset.completedPlays === '3'", timeout=25000)
                    cta_visible(page)
                    assert page.locator('.hero-media').bounding_box() == before
                    assert page.locator('.hero-call').inner_text() == label
                    page.screenshot(path=str(screenshots / f'{engine}-{width}-cta.png'))
                    await_no_focus = page.evaluate('document.activeElement === document.body')
                    assert await_no_focus, 'Natural completion must not steal focus'
                    page.locator('.hero-call').click()
                    page.wait_for_function("location.hash === '#call'")
                    page.wait_for_function("document.querySelector('#leadForm input[name=\"name\"]').matches(':focus')")
                    assert not page.locator('#leadForm input[name="consent"]').is_checked()
                    context.close()
                    results.append(f'{engine}: {path} three real plays, CTA, stable layout, form focus PASS')

                context, page = page_for(viewport={'width': 390, 'height': 844})
                page.goto(base + '/nl/')
                page.wait_for_function("document.querySelector('video').currentTime > 0.1")
                page.locator('[data-action="pause"]').click()
                paused_at = page.locator('video').evaluate('(v) => v.currentTime')
                page.wait_for_timeout(400)
                assert page.locator('video').evaluate('(v) => v.paused')
                assert abs(page.locator('video').evaluate('(v) => v.currentTime') - paused_at) < .1
                page.locator('[data-action="pause"]').click()
                page.wait_for_function("!document.querySelector('video').paused")
                page.locator('[data-action="sound"]').click()
                assert page.locator('video').evaluate('(v) => !v.muted')
                assert page.locator('[data-action="sound"]').get_attribute('aria-pressed') == 'true'
                page.locator('[data-action="skip"]').focus()
                page.keyboard.press('Enter')
                cta_visible(page)
                assert page.locator('.hero-call').evaluate('(e) => e === document.activeElement')
                context.close()
                results.append(f'{engine}: pause/resume, sound, keyboard skip/focus PASS')

                for scenario in ['reduced', 'no-js', 'blocked', 'error', 'timeout', 'motion-change']:
                    context, page = page_for(
                        reduced_motion='reduce' if scenario == 'reduced' else 'no-preference',
                        java_script_enabled=scenario != 'no-js')
                    media_requests = []
                    page.on('request', lambda req: media_requests.append(req.url) if '.mp4' in req.url else None)
                    if scenario == 'blocked':
                        page.add_init_script("HTMLMediaElement.prototype.play = function() { return Promise.reject(new DOMException('Blocked', 'NotAllowedError')); };")
                    if scenario == 'error':
                        page.route('**/*.mp4', lambda route: route.abort())
                    if scenario == 'timeout':
                        page.clock.install()
                        held_routes = []
                        page.route('**/*.mp4', lambda route: held_routes.append(route))
                    page.goto(base + '/nl/', wait_until='domcontentloaded')
                    if scenario == 'timeout':
                        page.clock.fast_forward(12500)
                    if scenario == 'motion-change':
                        page.wait_for_function("document.querySelector('video').currentTime > 0.1")
                        page.emulate_media(reduced_motion='reduce')
                    if scenario == 'no-js':
                        page.locator('.hero-call').wait_for(state='visible')
                        assert not page.locator('video').is_visible()
                    else:
                        cta_visible(page)
                    if scenario in ['no-js', 'reduced']:
                        assert not media_requests, media_requests
                    if scenario == 'timeout':
                        for route in held_routes:
                            route.abort()
                    context.close()
                    results.append(f'{engine}: {scenario} CTA fallback PASS')
                browser.close()
                assert not external, external
                assert not errors, errors
    finally:
        server.shutdown()
        server.server_close()
    print(json.dumps({'results': results, 'screenshots': str(screenshots),
                      'external_requests': 0, 'page_errors': 0}, indent=2))


if __name__ == '__main__':
    run()
