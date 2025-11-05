import React, { useEffect, useState } from "react";
import {
  Image,
  ScrollView,
  Share,
  Text,
  TouchableOpacity,
  View,
} from "react-native";
import BookmarksController from "../../controllers/BookmarksController";
import { Article } from "../../models/Article";

interface ArticleProps {
  route: { params: { article: Article } };
}

export default function ArticleScreen({ route }: ArticleProps) {
  const { article } = route.params;
  const [bookmarked, setBookmarked] = useState(false);

  useEffect(() => {
    (async () => {
      const all = await BookmarksController.getAll();
      console.log("RAM12", all)
      setBookmarked(!!all.find((a) => a.id === article.id));
    })();
  }, []);

  const onToggleBookmark = async () => {
    await BookmarksController.toggle(article);
    const all = await BookmarksController.getAll();
    setBookmarked(!!all.find((a) => a.id === article.id));
  };

  const onShare = async () => {
    await Share.share({ message: `${article.title}\n${article.url}` });
  };

  return (
    <ScrollView style={{ flex: 1, padding: 12 }}>
      {article.image && (
        <Image
          source={{ uri: article.image }}
          style={{ height: 200, borderRadius: 8 }}
        />
      )}
      <Text style={{ fontSize: 20, fontWeight: "bold", marginTop: 12 }}>
        {article.title}
      </Text>
      <Text style={{ color: "#666", marginTop: 6 }}>
        {article.source} • {new Date(article.publishedAt).toLocaleString()}
      </Text>
      <Text style={{ marginTop: 12 }}>
        {article.content || article.description}
      </Text>

      <View style={{ flexDirection: "row", marginTop: 16 }}>
        <TouchableOpacity
          onPress={onToggleBookmark}
          style={{ marginRight: 12 }}
        >
          <Text>{bookmarked ? "Remove Bookmark" : "Bookmark"}</Text>
        </TouchableOpacity>
        <TouchableOpacity onPress={onShare}>
          <Text>Share</Text>
        </TouchableOpacity>
      </View>
    </ScrollView>
  );
}
