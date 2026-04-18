import { defaultTheme, Provider } from "@adobe/react-spectrum";
import { BrowserRouter, Route, Routes } from "react-router";
import Navbar from "./components/Navbar";
import Chat from "./pages/Chat";
import Home from "./pages/Home";

export default function App() {
  return (
    <Provider theme={defaultTheme} colorScheme="dark">
      <BrowserRouter basename="/makeathon-2026-reply">
        <Navbar />
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/chat" element={<Chat />} />
        </Routes>
      </BrowserRouter>
    </Provider>
  );
}
