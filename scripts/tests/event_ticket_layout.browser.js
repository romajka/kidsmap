// Run with Playwright CLI run-code on an upcoming event with a ticket link.
async page => {
  const ticket = page.locator('.event-ticket');
  await page.emulateMedia({ reducedMotion: 'reduce' });

  const failures = [];
  for (const width of [320, 390, 767, 768, 810, 920, 921, 980, 1024, 1140, 1180, 1210, 1440]) {
    await page.setViewportSize({ width, height: 900 });
    const issues = await ticket.evaluate(async element => {
      await document.fonts.ready;
      const facts = element.querySelector('.event-ticket-facts');
      const timer = element.querySelector('.km-timer--poster');
      const action = element.querySelector('.event-ticket-action');
      if (!timer || !action?.querySelector('a')) {
        throw new Error('The event fixture needs a countdown and a visible ticket link');
      }

      const issues = [];
      const bounds = element.getBoundingClientRect();
      const intersects = (a, b) => Math.min(a.right, b.right) - Math.max(a.left, b.left) > 1
        && Math.min(a.bottom, b.bottom) - Math.max(a.top, b.top) > 1;
      const outside = (child, parent) => child.left < parent.left - 1 || child.right > parent.right + 1;

      if (bounds.left < -1 || bounds.right > document.documentElement.clientWidth + 1) {
        issues.push('the ticket exceeds the viewport');
      }
      const timerBounds = timer.getBoundingClientRect();
      const actionBounds = action.getBoundingClientRect();
      if (intersects(timerBounds, actionBounds)) issues.push('the countdown overlaps the ticket action');

      for (const cell of facts.children) {
        const cellBounds = cell.getBoundingClientRect();
        if (outside(cellBounds, facts.getBoundingClientRect())) issues.push(cell.className + ' exceeds the facts');
        if (intersects(cellBounds, timerBounds) || intersects(cellBounds, actionBounds)) {
          issues.push(cell.className + ' overlaps the countdown or ticket action');
        }
      }

      const day = element.querySelector('.event-date-day');
      const dateText = document.createRange();
      dateText.selectNodeContents(day);
      if (dateText.getClientRects().length !== 1) issues.push('the numbered day wraps');
      return issues;
    });
    if (issues.length) failures.push(width + 'px — ' + issues.join(', '));
  }
  if (failures.length) throw new Error(failures.join('\n'));
};
