"use client";

import { useEffect, useState } from "react";
import "./globals.css";
import Navbar from "@/components/ui/Navbar";
import AgentChatDrawer from "@/components/chat/AgentChatDrawer";
import { useAuthStore } from "@/store/useAuthStore";
import { Sparkles } from "lucide-react";

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const { loadFromStorage } = useAuthStore();

  useEffect(() => {
    loadFromStorage();
  }, [loadFromStorage]);

  return (
    <html lang="en" className="dark">
      <head>
        <title>AETHER INDIA — Luxury Heavyweight Streetwear & AI Operations</title>
        <meta
          name="description"
          content="Autonomous AI Business Operations Streetwear Platform powered by a 4-Agent LangGraph Multi-Agent Architecture."
        />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
      </head>
      <body className="bg-aether-950 text-white min-h-screen flex flex-col antialiased selection:bg-white selection:text-black">
        {/* Navigation Bar */}
        <Navbar onOpenChat={() => setIsChatOpen(true)} />

        {/* Main Content Viewport */}
        <main className="flex-1 max-w-7xl w-full mx-auto px-4 sm:px-6 lg:px-8 py-6">
          {children}
        </main>

        {/* Floating Quick AI Launcher Pill */}
        <div className="fixed bottom-6 right-6 z-40">
          <button
            onClick={() => setIsChatOpen(true)}
            className="flex items-center gap-2 px-4 py-3 rounded-full bg-white text-black font-mono text-xs font-bold shadow-2xl hover:bg-aether-200 transition-all hover:scale-105 group border border-white/20"
          >
            <Sparkles className="w-4 h-4 text-street-amber group-hover:rotate-12 transition-transform" />
            <span>AI CONCIERGE</span>
            <span className="w-2 h-2 rounded-full bg-street-emerald animate-ping" />
          </button>
        </div>

        {/* Slide-out 4-Agent LangGraph Multi-Agent Chat Drawer */}
        <AgentChatDrawer isOpen={isChatOpen} onClose={() => setIsChatOpen(false)} />

        {/* Luxury Streetwear Minimal Footer */}
        <footer className="border-t border-aether-850 bg-aether-950/80 py-8 px-4 text-center text-xs font-mono text-aether-500">
          <div className="max-w-7xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <span className="font-bold text-white tracking-widest uppercase">AETHER INDIA</span>
              <span>// 4-Agent LangGraph AI Ops</span>
            </div>
            <div className="flex items-center gap-4 text-aether-400">
              <span>BlueDart &amp; Delhivery Logistics</span>
              <span>•</span>
              <span>₹ INR Pricing</span>
              <span>•</span>
              <span>ChromaDB RAG</span>
            </div>
            <div className="text-aether-600">
              © {new Date().getFullYear()} AETHER INDIA Pvt. Ltd. All rights reserved.
            </div>
          </div>
        </footer>
      </body>
    </html>
  );
}
