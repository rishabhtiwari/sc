import { createStackNavigator } from "@react-navigation/stack";
import ArticleScreen from "../views/article/Article";
import Bookmarks from "../views/bookmarks/Bookmarks";
import Home from "../views/home/Home";
import React from "react";

export type RootStackParamList = {
  Home: undefined;
  Article: { id?: string };
  Bookmarks: undefined;
};

const Stack = createStackNavigator<RootStackParamList>();

interface AppNavigatorProps {
  toggleTheme: () => void;
}

interface HomeProps {
  toggleTheme: () => void;
}

const AppNavigator: React.FC<AppNavigatorProps> = ({ toggleTheme }) => {
  return (
    <Stack.Navigator>
      <Stack.Screen name="Home" options={{ title: "InShorts Clone" }}>
        {(props) => <Home {...props} toggleTheme={toggleTheme} />}
      </Stack.Screen>
      <Stack.Screen
        name="Article"
        component={ArticleScreen}
        options={{ title: "Article" }}
      />
      <Stack.Screen
        name="Bookmarks"
        component={Bookmarks}
        options={{ title: "Bookmarks" }}
      />
    </Stack.Navigator>
  );
};

export default AppNavigator;
