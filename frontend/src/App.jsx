// src/App.jsx
import React, { useState, useEffect, useRef } from "react";
import "./App.css";
import ChatInterface from "./components/ChatInterface";

const App = () => {
  return (
    <div className="app-wrapper">
      <ChatInterface />
    </div>
  );
};

export default App;
