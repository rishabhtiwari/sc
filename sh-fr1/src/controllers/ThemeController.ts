import AsyncStorage from "@react-native-async-storage/async-storage";
import { useEffect, useState } from "react";

const THEME_KEY = "APP_THEME_V1";

export class ThemeController {
  static useTheme(): ["light" | "dark", () => Promise<void>] {
    const [theme, setTheme] = useState<"light" | "dark">("light");

    useEffect(() => {
      (async () => {
        const t = await AsyncStorage.getItem(THEME_KEY);
        if (t === "dark" || t === "light") setTheme(t);
      })();
    }, []);

    const toggleTheme = async () => {
      const next = theme === "light" ? "dark" : "light";
      setTheme(next);
      await AsyncStorage.setItem(THEME_KEY, next);
    };

    return [theme, toggleTheme];
  }
}
