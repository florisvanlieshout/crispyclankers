/* Three completed plays, never a timer pretending that playback happened. */
(function () {
  'use strict';
  var box = document.querySelector('.hero-media');
  if (!box) return;
  var video = box.querySelector('video');
  var finale = box.querySelector('.hero-finale');
  var cta = box.querySelector('.hero-call');
  var controls = box.querySelector('.hero-controls');
  var pause = controls.querySelector('[data-action="pause"]');
  var sound = controls.querySelector('[data-action="sound"]');
  var motion = window.matchMedia('(prefers-reduced-motion: reduce)');
  var completed = 0;
  var finished = false;
  var startupTimer;

  function finish() {
    if (finished) return;
    finished = true;
    clearTimeout(startupTimer);
    var restoreFocus = controls.contains(document.activeElement);
    video.pause();
    video.removeAttribute('src');
    video.load();
    video.remove();
    controls.hidden = true;
    finale.hidden = false;
    box.dataset.state = 'cta';
    if (restoreFocus) cta.focus({preventScroll: true});
  }

  cta.addEventListener('click', function () {
    // Navigation only: never submit a lead or bypass explicit call consent.
    var field = document.querySelector('#leadForm input[name="name"]');
    if (field) {
      // Let the anchor's default fragment navigation finish before moving focus.
      setTimeout(function () { field.focus({preventScroll: true}); }, 0);
    }
  });

  if (motion.matches) { finish(); return; }
  motion.addEventListener('change', function (event) {
    if (event.matches) finish();
  });
  video.addEventListener('error', finish);
  video.addEventListener('playing', function () {
    clearTimeout(startupTimer);
    pause.textContent = pause.dataset.pause;
  });
  video.addEventListener('pause', function () {
    pause.textContent = pause.dataset.resume;
  });

  function play() {
    if (finished) return;
    // A blocked play promise or a source that never starts must not hide the CTA.
    clearTimeout(startupTimer);
    startupTimer = setTimeout(finish, 12000);
    try {
      var attempt = video.play();
      if (attempt && attempt.catch) attempt.catch(finish);
    } catch (error) { finish(); }
  }

  video.addEventListener('ended', function () {
    if (finished) return;
    completed += 1;
    box.dataset.completedPlays = String(completed);
    if (completed >= 3) { finish(); return; }
    video.currentTime = 0;
    play();
  });
  pause.addEventListener('click', function () {
    if (video.paused) play();
    else { clearTimeout(startupTimer); video.pause(); }
  });
  sound.addEventListener('click', function () {
    video.muted = !video.muted;
    sound.textContent = video.muted ? sound.dataset.sound : sound.dataset.mute;
    sound.setAttribute('aria-pressed', String(!video.muted));
  });
  controls.querySelector('[data-action="skip"]').addEventListener('click', finish);

  video.muted = true;
  video.src = video.dataset.src;
  video.hidden = false;
  finale.hidden = true;
  controls.hidden = false;
  box.dataset.state = 'playing';
  play();
})();
