import React, { useState } from "react";
import PropTypes from "prop-types";
import { calculateGreenSignalTime } from "../utils/greenSignalCalculator";

const VehicleStats = ({ counts, totalUniqueVehicles, isDarkMode }) => {
  const [gst, setGst] = useState(null);

  const statCards = [
    {
      label: "Cars",
      count: counts.car,
      color: isDarkMode ? "blue" : "sky",
      icon: "🚗",
    },
    {
      label: "Trucks",
      count: counts.truck,
      color: isDarkMode ? "emerald" : "teal",
      icon: "🚛",
    },
    {
      label: "Motorbikes",
      count: counts.motorbikes,
      color: isDarkMode ? "yellow" : "amber",
      icon: "🏍️",
    },
    {
      label: "Others",
      count: counts.other,
      color: isDarkMode ? "purple" : "violet",
      icon: "🚐",
    },
  ];

  const calculateGST = () => {
    const time = calculateGreenSignalTime({
      totalVehicles: totalUniqueVehicles,
      cars: counts.car,
      trucks: counts.truck,
      motorbikes: counts.motorbikes,
      others: counts.other,
    });
    setGst(time);
  };

  return (
    <div className="mt-8 space-y-8">
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
        {statCards.map(({ label, count, color, icon }) => (
          <div
            key={label}
            className={`rounded-xl p-6 transition-all duration-300 transform hover:scale-105 ${
              isDarkMode
                ? `bg-slate-800 border border-slate-600 hover:bg-slate-700`
                : `bg-white border border-${color}-100 hover:shadow-lg`
            }`}
          >
            <div className="flex items-center justify-between">
              <span className="text-3xl" role="img" aria-label={label}>
                {icon}
              </span>
              <span
                className={`${
                  isDarkMode ? "text-white" : `text-${color}-600`
                } text-xl font-bold`}
              >
                {count}
              </span>
            </div>
            <h3
              className={`mt-2 ${
                isDarkMode ? "text-slate-200" : `text-${color}-900`
              } font-medium`}
            >
              {label}
            </h3>
          </div>
        ))}
      </div>

      <div
        className={`rounded-xl p-8 transition-colors duration-300 ${
          isDarkMode
            ? "bg-slate-800 border-slate-600"
            : "bg-white border-[#86BCA6]/20"
        } border`}
      >
        <div className="text-center">
          <h2 className={isDarkMode ? "text-slate-200" : "text-indigo-900"}>
            Total Vehicles
          </h2>
          <p
            className={`text-5xl font-bold mt-2 ${
              isDarkMode ? "text-white" : "text-indigo-600"
            }`}
          >
            {totalUniqueVehicles}
          </p>
        </div>

        <div className="mt-8">
          <button
            onClick={calculateGST}
            className={`w-full py-3 px-6 rounded-lg text-lg font-semibold transition-all duration-300 transform hover:scale-[1.02] focus:outline-none focus:ring-2 focus:ring-opacity-50 ${
              isDarkMode
                ? "bg-gradient-to-r from-cyan-600 to-teal-600 hover:from-cyan-700 hover:to-teal-700 text-white shadow-lg shadow-cyan-500/25 ring-1 ring-cyan-400/20"
                : "bg-gradient-to-r from-emerald-500 to-teal-600 hover:from-emerald-600 hover:to-teal-700 text-white shadow-lg shadow-teal-500/25"
            }`}
          >
            Calculate Green Signal Time
          </button>
        </div>

        {gst !== null && (
          <div
            className={`mt-6 rounded-lg p-6 border-l-4 border-green-500 animate-fade-in ${
              isDarkMode ? "bg-slate-700" : "bg-white"
            }`}
          >
            <div className="flex items-center space-x-4">
              <div
                className={`p-3 rounded-full ${
                  isDarkMode ? "bg-slate-600" : "bg-green-100"
                }`}
              >
                <span
                  className="text-2xl"
                  role="img"
                  aria-label="traffic light"
                >
                  🚦
                </span>
              </div>
              <div>
                <p className={isDarkMode ? "text-slate-300" : "text-gray-600"}>
                  Recommended Time
                </p>
                <p
                  className={`text-3xl font-bold ${
                    isDarkMode ? "text-green-400" : "text-green-600"
                  }`}
                >
                  {gst} seconds
                </p>
              </div>
            </div>
          </div>
        )}
      </div>

      <div
        className={`rounded-lg p-4 text-sm ${
          isDarkMode
            ? "bg-slate-800 text-slate-300"
            : "bg-gray-50 text-gray-600"
        }`}
      >
        <ul className="space-y-1 list-disc list-inside">
          <li>All counts represent unique vehicles detected</li>
          <li>Each vehicle is counted only once when first detected</li>
        </ul>
      </div>
    </div>
  );
};

VehicleStats.propTypes = {
  counts: PropTypes.shape({
    car: PropTypes.number.isRequired,
    truck: PropTypes.number.isRequired,
    motorbikes: PropTypes.number.isRequired,
    other: PropTypes.number.isRequired,
  }).isRequired,
  totalUniqueVehicles: PropTypes.number.isRequired,
};

export default VehicleStats;
