        self.on_log("Launching Chrome window with persistent profile...", "INFO")
        try:
            if not self._playwright:
                self._playwright = sync_playwright().start()

            user_data_dir = str(self.config.get_chrome_profile_dir())
            launch_args = ["--no-default-browser-check", "--no-first-run", "--start-maximized"]
            channel = "chrome" if self.config.use_system_chrome else None

            try:
                self._context = self._playwright.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir, headless=False, channel=channel,
                    args=launch_args, no_viewport=True,
                )
            except Exception:
                self._context = self._playwright.chromium.launch_persistent_context(
                    user_data_dir=user_data_dir, headless=False,
                    args=launch_args, no_viewport=True,
                )

            self._page = self._context.pages[0] if self._context.pages else self._context.new_page()
            self._browser_open = True
            self.on_log("Navigating to https://mewe.com ...", "INFO")
            self._page.goto("https://mewe.com", wait_until="domcontentloaded", timeout=45000)

            self.on_status("Chrome Ready (MeWe loaded)")
            self.on_log(
                "Chrome opened. Log in, open the page with Follow buttons, then press START.",
                "SUCCESS",
            )
        except Exception as e:
            self._browser_open = False
            self.on_log(f"Failed to launch Chrome: {e}", "ERROR")
            self.on_status("Launch Error")

    def _do_close(self) -> None:
        self._running = False
        for closer in (
            lambda: self._context.close() if self._context else None,
            lambda: self._playwright.stop() if self._playwright else None,
