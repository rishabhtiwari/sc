import {
  DarkTheme,
  DefaultTheme,
  NavigationContainer,
} from "@react-navigation/native";
import React from "react";
import { ThemeController } from "./src/controllers/ThemeController";
import AppNavigator from "./src/navigation/AppNavigator";

export default function App() {
  const [theme, toggleTheme] = ThemeController.useTheme();

  return (
    <NavigationContainer theme={theme === "dark" ? DarkTheme : DefaultTheme}>
      <AppNavigator toggleTheme={toggleTheme} />
    </NavigationContainer>
  );
}
