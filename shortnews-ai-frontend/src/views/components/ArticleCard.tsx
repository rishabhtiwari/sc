import React from "react";
import { Image, Text, TouchableOpacity, View } from "react-native";
import { Article } from "../../models/Article";

interface Props {
  article: Article;
  onPress: () => void;
}

export default function ArticleCard({ article, onPress }: Props) {
  return (
    <TouchableOpacity
      onPress={onPress}
      style={{ marginBottom: 12, flexDirection: "row", alignItems: "center" }}
    >
      {article.imageUrl && (
        <Image
          source={{ uri: article.imageUrl }}
          style={{ width: 100, height: 70, borderRadius: 8, marginRight: 12 }}
        />
      )}
      <View style={{ flex: 1 }}>
        <Text numberOfLines={2} style={{ fontWeight: "bold" }}>
          {article.title}
        </Text>
        <Text style={{ color: "#666", marginTop: 4 }}>{article.source}</Text>
      </View>
    </TouchableOpacity>
  );
}
