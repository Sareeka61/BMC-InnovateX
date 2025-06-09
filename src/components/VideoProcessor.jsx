import React, { useRef, useEffect, useState } from "react";
import PropTypes from "prop-types";

const VideoProcessor = ({
  video,
  isProcessing,
  onProcess,
  model,
  trackerRef,
  onUpdateCounts,
  onUpdateTotalVehicles,
  isDarkMode,
}) => {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const [dimensions, setDimensions] = useState({ width: 0, height: 0 });

  useEffect(() => {
    if (videoRef.current) {
      videoRef.current.src = video;

      videoRef.current.onloadeddata = () => {
        const width = videoRef.current.videoWidth;
        const height = videoRef.current.videoHeight;
        setDimensions({ width, height });

        // Set canvas dimensions to match video
        if (canvasRef.current) {
          canvasRef.current.width = width;
          canvasRef.current.height = height;
        }
      };
    }
  }, [video]);

  const processVideo = async () => {
    if (!video || !model || !trackerRef.current) {
      console.error("Missing required resources");
      return;
    }

    const videoElement = videoRef.current;
    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");

    const detectObjects = async () => {
      if (videoElement.paused || videoElement.ended) {
        onProcess(false);
        return;
      }

      try {
        // Always clear the canvas before drawing
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Ensure video frame is drawn properly
        ctx.drawImage(videoElement, 0, 0, canvas.width, canvas.height);

        // Detect objects
        const predictions = await model.detect(canvas);

        // Update tracker with detections
        trackerRef.current.update(predictions);

        // Draw bounding boxes
        predictions.forEach((prediction) => {
          if (
            ["car", "truck", "motorcycle", "bus"].includes(prediction.class)
          ) {
            const [x, y, width, height] = prediction.bbox;

            // Draw bounding box with better visibility
            ctx.strokeStyle = "#00FF00";
            ctx.lineWidth = 3;
            ctx.strokeRect(x, y, width, height);

            // Draw label background for better readability
            const label = `${prediction.class} ${Math.round(
              prediction.score * 100
            )}%`;
            ctx.font = "16px Arial";
            const labelWidth = ctx.measureText(label).width;

            ctx.fillStyle = "rgba(0, 255, 0, 0.7)";
            ctx.fillRect(x, y > 20 ? y - 24 : y + 2, labelWidth + 8, 20);

            // Draw label text
            ctx.fillStyle = "#000000";
            ctx.fillText(label, x + 4, y > 20 ? y - 8 : y + 18);
          }
        });

        // Update counts and request next frame
        onUpdateCounts(trackerRef.current.getFrameCounts());
        onUpdateTotalVehicles(trackerRef.current.getTotalUniqueVehicles());
        requestAnimationFrame(detectObjects);
      } catch (error) {
        console.error("Detection error:", error);
        onProcess(false);
      }
    };

    try {
      // Ensure video is playing
      await videoElement.play();
      detectObjects();
    } catch (error) {
      console.error("Video playback error:", error);
      onProcess(false);
    }
  };

  return (
    <div className="space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="relative">
          <h3
            className={`text-lg font-semibold mb-2 ${
              isDarkMode ? "text-white" : "text-slate-800"
            }`}
          >
            Original Video
          </h3>
          <video
            ref={videoRef}
            style={{ width: "100%", height: "auto", maxHeight: "400px" }}
            className="rounded-lg shadow-lg object-contain bg-black"
            controls
          />
        </div>
        <div className="relative">
          <h3
            className={`text-lg font-semibold mb-2 ${
              isDarkMode ? "text-white" : "text-slate-800"
            }`}
          >
            Detection View
          </h3>
          <canvas
            ref={canvasRef}
            style={{
              width: "100%",
              height: "auto",
              maxHeight: "400px",
              backgroundColor: "#000",
            }}
            className="rounded-lg shadow-lg object-contain"
          />
        </div>
      </div>
      <button
        onClick={() => {
          onProcess(true);
          processVideo();
        }}
        disabled={isProcessing}
        className={`w-full py-2 px-4 rounded-lg text-white font-semibold ${
          isProcessing
            ? "bg-gray-400 cursor-not-allowed"
            : isDarkMode
            ? "bg-blue-600 hover:bg-blue-700"
            : "bg-blue-600 hover:bg-blue-700"
        }`}
      >
        {isProcessing ? "Processing..." : "Start Detection"}
      </button>
    </div>
  );
};

VideoProcessor.propTypes = {
  video: PropTypes.string.isRequired,
  isProcessing: PropTypes.bool.isRequired,
  onProcess: PropTypes.func.isRequired,
  model: PropTypes.object,
  trackerRef: PropTypes.object.isRequired,
  onUpdateCounts: PropTypes.func.isRequired,
  onUpdateTotalVehicles: PropTypes.func.isRequired,
};

export default VideoProcessor;
