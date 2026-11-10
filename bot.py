
    def _run_loop(self) -> None:
        self.on_log("People List scanner started.", "SUCCESS")

        while not self._stop_event.is_set():
            if not self._pause_event.is_set():
                time.sleep(0.5)
                continue

            try:
                candidates = []

                for sel in [
                    "button:has-text('Follow')",
                    "button:has-text('+ Follow')",
                    "[data-testid*='follow']"
                ]:
                    loc = self._page.locator(sel)

                    for i in range(loc.count()):
                        btn = loc.nth(i)
                        if self._is_safe_follow_button(btn):
                            candidates.append(btn)

                self.stats["profiles_scanned"] += len(candidates)
                self.on_stats(self.stats)

                if candidates:
                    self.on_log(
                        f"Found {len(candidates)} Follow button(s). "
                        "Review and follow manually.",
                        "SUCCESS"
                    )
                else:
                    self.on_log(
                        "No visible Follow buttons found.",
                        "INFO"
                    )

                if self.config.auto_scroll_enabled:
                    moved = self._page.evaluate("""() => {
                        const elements = [...document.querySelectorAll('*')];
                        const scrollables = elements.filter(el => {
                            const s = getComputedStyle(el);
                            return /(auto|scroll)/.test(s.overflowY) &&
                                el.scrollHeight > el.clientHeight + 100;
                        });

                        scrollables.sort((a, b) =>
                            b.scrollHeight - a.scrollHeight
                        );

                        const target = scrollables[0];

                        if (target) {
                            const before = target.scrollTop;
                            target.scrollBy({
                                top: 600,
                                behavior: 'instant'
                            });
                            return target.scrollTop !== before;
                        }

                        const before = window.scrollY;
                        window.scrollBy(0, 600);
                        return window.scrollY !== before;
                    }""")

                    if moved:
                        self.stats["scrolls_performed"] += 1
                        self.on_log(
                            "People List scroll attempted.",
                            "INFO"
                        )
                    else:
                        self.on_log(
                            "No scroll movement detected. "
                            "Check that People List is open.",
                            "WARNING"
                        )

                    self.on_stats(self.stats)

                time.sleep(self.config.scroll_pause_seconds)

            except Exception as err:
                self.stats["errors"] += 1
                self.on_stats(self.stats)
                self.on_log(f"Scanner error: {err}", "ERROR")
                time.sleep(2)
