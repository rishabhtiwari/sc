import React from "react";
import { ThemeController, AppNavigator } from "../src";

export default function Page() {
  const [theme, toggleTheme] = ThemeController.useTheme();

  return <AppNavigator toggleTheme={toggleTheme} />;
}
