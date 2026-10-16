# Admin sidebar fix

User-authorized scope: repair burger/sidebar layout in the current dirty WORKTREE.
LOCAL HEAD: e4e05cc213b34e2d771ecb854901bfd016d1db51, task33-progress.

Cause: the custom layout disables AdminLTE hover expansion by constraining the
sidebar width, while vendor rules still reveal legacy labels and widen links on
hover/focus. AdminLTE switches its sidebar at 992px; custom layout reserves space
from 768px without resetting the vendor negative sidebar margin.

1. Render both actual base templates with fictional navigation and installed
   Jazzmin/AdminLTE assets, no database or production environment.
2. Reproduce label leakage on hover/focus and tablet clipping in Chromium.
3. Make desktop/tablet sidebar position, inner widths and hidden labels agree
   with its expanded/collapsed state. Keep the existing mobile drawer behavior.
4. Bump CSS cache versions in both base templates and the stylesheet import.
5. Check RU/AZ/EN, 375/390/768/900/991/992/1024/1280/1440px, hover,
   keyboard, repeated toggle, mobile backdrop, screenshots, console and static
   requests. Record the exact limitations of this template fixture.

No business rules, data, commit, push or deployment in this scope.
