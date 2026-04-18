import { Content, Heading, View } from "@adobe/react-spectrum";

export default function Home() {
  return (
    <View padding="size-400">
      <Heading level={1}>Campus Co-Pilot</Heading>
      <Content>
        <p>Your AI-powered career guide for TUM students.</p>
      </Content>
    </View>
  );
}
