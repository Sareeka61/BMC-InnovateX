import React, { useState, useEffect } from "react";
import * as cocoSsd from "@tensorflow-models/coco-ssd";
import VideoUploader from "./components/VideoUploader";
import VideoProcessor from "./components/VideoProcessor";
import VehicleStats from "./components/VehicleStats";
import VehicleTracker from "./components/VehicleTracker";
import * as tf from "@tensorflow/tfjs";

function App() {
  const [isDarkMode, setIsDarkMode] = useState(false);
  const [video, setVideo] = useState(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [model, setModel] = useState(null);
  const [counts, setCounts] = useState({
    car: 0,
    truck: 0,
    motorbikes: 0,
    other: 0,
  });
  const [totalUniqueVehicles, setTotalUniqueVehicles] = useState(0);
  const trackerRef = React.useRef(null);

  useEffect(() => {
    const loadModel = async () => {
      try {
        // Initialize TensorFlow.js first
        await tf.ready();
        // Load model with specific configuration
        const loadedModel = await cocoSsd.load({
          base: "mobilenet_v2",
        });
        setModel(loadedModel);
        trackerRef.current = new VehicleTracker();
      } catch (error) {
        console.error("Error loading model:", error);
      }
    };
    loadModel();
  }, []);

  const handleVideoUpload = (videoUrl) => {
    setVideo(videoUrl);
    resetCounts();
  };

  const resetCounts = () => {
    setCounts({
      car: 0,
      truck: 0,
      motorbikes: 0,
      other: 0,
    });
    setTotalUniqueVehicles(0);
    trackerRef.current = new VehicleTracker();
  };

  return (
    <div
      className={`min-h-screen transition-colors duration-300 ${
        isDarkMode
          ? "bg-gradient-to-b from-slate-950 via-slate-900 to-slate-950 text-white"
          : "bg-gradient-to-b from-[#F1F5F4] to-[#E7EFED] text-slate-800"
      }`}
    >
      {/* Navbar */}
      <nav
        className={`${
          isDarkMode
            ? "bg-slate-800/95 border-slate-600"
            : "bg-white/80 border-[#86BCA6]/20"
        } backdrop-blur-md border-b shadow-lg transition-colors duration-300`}
      >
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-4">
              <div className="text-3xl filter drop-shadow-lg">🚦</div>
              <div>
                <h1
                  className={`text-2xl font-bold tracking-tight ${
                    isDarkMode
                      ? "text-slate-100 drop-shadow-md"
                      : "text-[#2A4849]"
                  }`}
                >
                  Traffix
                </h1>
                <p
                  className={`text-sm ${
                    isDarkMode ? "text-slate-200" : "text-[#7C8B8C]"
                  }`}
                >
                  Smart Mobility for Smart Cities
                </p>
              </div>
            </div>
            <div className="flex items-center space-x-4">
              <button
                onClick={() => setIsDarkMode(!isDarkMode)}
                className={`p-2 rounded-full transition-all duration-300 ${
                  isDarkMode
                    ? "bg-slate-700 text-yellow-300 hover:bg-slate-600 ring-1 ring-slate-500"
                    : "bg-gray-100 text-gray-600 hover:bg-gray-200"
                }`}
              >
                {isDarkMode ? "🌙" : "☀️"}
              </button>
              {model ? (
                <span
                  className={`flex items-center px-4 py-2 rounded-full border transition-all duration-300 ${
                    isDarkMode
                      ? "bg-slate-700 border-slate-500 text-slate-100 ring-1 ring-slate-400/20"
                      : "bg-[#D7EDE2] border-[#86BCA6] text-[#2A4849]"
                  }`}
                >
                  <span
                    className={`w-2 h-2 rounded-full mr-2 ${
                      isDarkMode
                        ? "bg-emerald-400 shadow-lg shadow-emerald-400/50"
                        : "bg-[#2A4849]"
                    }`}
                  ></span>
                  <span className="font-medium">System Active</span>
                </span>
              ) : (
                <span
                  className={`flex items-center px-4 py-2 rounded-full border transition-all duration-300 ${
                    isDarkMode
                      ? "bg-slate-700 border-slate-600 text-slate-200"
                      : "bg-[#F1F5F4] border-[#7C8B8C]/30"
                  }`}
                >
                  <span
                    className={`w-2 h-2 rounded-full mr-2 animate-pulse ${
                      isDarkMode
                        ? "bg-blue-400 shadow-lg shadow-blue-400/50"
                        : "bg-[#86BCA6]"
                    }`}
                  ></span>
                  <span>Initializing...</span>
                </span>
              )}
            </div>
          </div>
        </div>
      </nav>

      <main className="container mx-auto px-4 py-12">
        <div className="max-w-6xl mx-auto space-y-8">
          <div
            className={`rounded-2xl transition-all duration-300 ${
              isDarkMode
                ? "bg-slate-800/80 border-slate-600 ring-1 ring-white/10"
                : "bg-white border-[#86BCA6]/20 shadow-lg"
            } border`}
          >
            <div className="p-8">
              <VideoUploader
                onVideoUpload={handleVideoUpload}
                onResetCounts={resetCounts}
                className="mb-8"
                isDarkMode={isDarkMode}
              />

              {video ? (
                <VideoProcessor
                  video={video}
                  isProcessing={isProcessing}
                  onProcess={setIsProcessing}
                  model={model}
                  trackerRef={trackerRef}
                  onUpdateCounts={setCounts}
                  onUpdateTotalVehicles={setTotalUniqueVehicles}
                  isDarkMode={isDarkMode}
                />
              ) : (
                <div className="text-center py-24">
                  <div className="text-5xl mb-6 filter drop-shadow-lg">📹</div>
                  <p
                    className={`text-xl font-medium mb-2 ${
                      isDarkMode ? "text-white" : "text-[#2A4849]"
                    }`}
                  >
                    Begin Your Traffic Analysis
                  </p>
                  <p
                    className={isDarkMode ? "text-slate-200" : "text-[#7C8B8C]"}
                  >
                    Upload traffic footage to start intelligent monitoring
                  </p>
                </div>
              )}
            </div>
          </div>

          <VehicleStats
            counts={counts}
            totalUniqueVehicles={totalUniqueVehicles}
            isDarkMode={isDarkMode}
          />
        </div>
      </main>

      <footer
        className={`border-t mt-12 transition-colors duration-300 ${
          isDarkMode
            ? "border-slate-800 bg-slate-900/50"
            : "border-[#86BCA6]/20"
        }`}
      >
        <div className="max-w-7xl mx-auto px-4 py-8 text-center">
          <p className={isDarkMode ? "text-slate-300" : "text-[#7C8B8C]"}>
            Built by Team Synergy
          </p>
        </div>
      </footer>
    </div>
  );
}

export default App;
