import VisualEditor from "@/components/graphs/editor/VisualEditor";
import type { GraphLoaderData } from "@/router/loaders";
import { useLoaderData, useNavigation } from "react-router-dom";

export function GraphEditorPage() {

  const result = useLoaderData<GraphLoaderData>();
  const navigation = useNavigation();

  if (navigation.state === "loading") {
    //return <h1>Loading!</h1>;
  }

  return (
      <VisualEditor graph={result.graph}/>
  )
}
