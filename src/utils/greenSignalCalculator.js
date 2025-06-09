export function calculateGreenSignalTime({
  numLanes = 1,
  totalVehicles,
  motorbikes,
  cars,
  trucks,
  others,
  processingTime = 1, // in seconds
  lagStart = 2, // startup lag for 1st vehicle
  minGreen = 10, // minimum green signal time
  maxGreen = 45, // maximum green signal time
}) {
  const vehicleTypes = [
    { count: motorbikes, baseTime: 1 },
    { count: cars, baseTime: 2 },
    { count: trucks, baseTime: 5 },
    { count: others, baseTime: 3 },
  ];

  let totalTime = 0;
  let vehicleIndex = 1;

  for (const { count, baseTime } of vehicleTypes) {
    for (let i = 0; i < count; i++) {
      let extraLag = 0;
      if (vehicleIndex === 1) {
        extraLag = lagStart;
      } else if (vehicleIndex <= 4) {
        extraLag = 0.5;
      } else if (vehicleIndex <= 10) {
        extraLag = 1;
      } else {
        extraLag = 1.5;
      }

      const vehicleTime = baseTime + extraLag;
      totalTime += vehicleTime;
      vehicleIndex++;
    }
  }

  const baseGreenTime = totalTime / (numLanes + 1) + processingTime;
  return Math.ceil(Math.max(minGreen, Math.min(maxGreen, baseGreenTime)));
}
