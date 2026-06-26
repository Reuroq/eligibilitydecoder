/* Eligibility Decoder — NCAA age-based 5-year eligibility checker.
   Estimate only; the school's compliance office makes the official determination. */
(function () {
  var CUR = 2026; // the 2026-27 season is the next one to be played

  var enroll = document.getElementById('f_enroll');
  if (enroll) {
    for (var y = 2030; y >= 2014; y--) {
      var o = document.createElement('option');
      o.value = String(y); o.textContent = 'Fall ' + y;
      enroll.appendChild(o);
    }
    enroll.value = '2024';
  }

  var go = document.getElementById('f_go');
  if (!go) return;

  go.addEventListener('click', function () {
    var res = document.getElementById('result');
    var dobStr = document.getElementById('f_dob').value;
    var enrollY = parseInt(document.getElementById('f_enroll').value, 10);
    var seasons = parseInt(document.getElementById('f_seasons').value, 10);
    res.hidden = false;

    if (!dobStr) {
      res.className = 'result err';
      res.innerHTML = '<p>Please enter your birth date so we can compute the age-based clock.</p>';
      return;
    }
    var dob = new Date(dobStr + 'T00:00:00');
    var b19y = dob.getFullYear() + 19;
    // "academic year following the 19th birthday": the fall on/after the 19th birthday.
    // 19th birthday in Aug or later -> the next fall; otherwise the same fall.
    var fallAfter19 = (dob.getMonth() >= 7) ? b19y + 1 : b19y;
    var clockStart = Math.min(enrollY, fallAfter19);

    // New model: 5 continuous years from clockStart; "years left" = window years still ahead.
    var newLeft = Math.max(0, Math.min(5, (clockStart + 5) - CUR));
    // Old model: up to 4 seasons of competition within a 5-year clock from enrollment.
    var oldClockLeft = Math.max(0, (enrollY + 5) - CUR);
    var oldLeft = Math.max(0, Math.min(4 - seasons, oldClockLeft));
    var transition = enrollY <= 2026;

    var best, basis;
    if (transition) {
      if (newLeft >= oldLeft) { best = newLeft; basis = 'new'; }
      else { best = oldLeft; basis = 'old'; }
    } else { best = newLeft; basis = 'new'; }

    var h = '';
    if (best <= 0) {
      h += '<div class="rbig rzero">No eligibility remaining</div>';
      h += '<p>Based on what you entered, your five-year window has closed. Ask your compliance office whether any exception (active-duty military, official religious mission, or pregnancy) could apply.</p>';
    } else {
      var yr = best === 1 ? 'year' : 'years';
      h += '<div class="rbig">~' + best + ' ' + yr + ' of eligibility left</div>';
      h += '<p class="rsub">Estimated going forward, starting with the 2026&ndash;27 season.</p>';
    }

    h += '<div class="rbreak">';
    if (transition) {
      h += '<div class="rrow' + (basis === 'new' ? ' win' : '') + '"><span>New age-based model</span><b>' + newLeft + ' ' + (newLeft === 1 ? 'yr' : 'yrs') + '</b></div>';
      h += '<div class="rrow' + (basis === 'old' ? ' win' : '') + '"><span>Old 4-in-5 rules</span><b>' + oldLeft + ' ' + (oldLeft === 1 ? 'yr' : 'yrs') + '</b></div>';
      h += '<p class="rsmall">You\'re a current / 2026 athlete, so your school applies <strong>whichever is more favorable</strong> — here, the <strong>' + (basis === 'new' ? 'new model' : 'old rules') + '</strong>.</p>';
    } else {
      h += '<div class="rrow win"><span>New age-based model</span><b>' + newLeft + ' ' + (newLeft === 1 ? 'yr' : 'yrs') + '</b></div>';
      h += '<p class="rsmall">You first enroll in fall ' + enrollY + ', so you\'re <strong>fully under the new model</strong> (no old-rules comparison).</p>';
    }
    h += '</div>';

    if (fallAfter19 < enrollY) {
      var lost = enrollY - clockStart;
      h += '<div class="rflag">&#9888;&#65039; Your five-year clock started in <strong>' + clockStart + '</strong> — the academic year after you turned 19 — which is <strong>before</strong> you enrolled (fall ' + enrollY + '). That delayed-enrollment age penalty costs you roughly <strong>' + lost + ' ' + (lost === 1 ? 'year' : 'years') + '</strong>. More on <a href="/transfers-juco-international.html">JUCO, international &amp; delayed enrollment</a>.</div>';
    }

    h += '<p class="rcaveat">This is an estimate, not a ruling. Your school\'s compliance office makes the official determination, and exceptions can pause the clock. The rule was adopted June 23, 2026 and may face legal challenges. <a href="/the-rule-explained.html">How the rule works &rarr;</a></p>';

    res.className = 'result ok';
    res.innerHTML = h;
    try { res.scrollIntoView({ behavior: 'smooth', block: 'nearest' }); } catch (e) {}
  });
})();
