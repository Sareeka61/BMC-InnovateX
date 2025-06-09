class VehicleTracker {
  constructor(maxDisappeared = 300, maxReidentifyFrames = 600) {
    this.vehicles = new Map(); // Map of vehicle ID to { centroid, type, disappeared, bbox, lastSeen }
    this.disappearedVehicles = new Map(); // Store recently disappeared vehicles
    this.nextId = 0;
    this.maxDisappeared = maxDisappeared; // Frames before moving to disappeared (~10s at 30 FPS)
    this.maxReidentifyFrames = maxReidentifyFrames; // Frames to keep disappeared vehicles (~20s at 30 FPS)
    this.totalUniqueVehicles = 0; // Total unique vehicles
    this.uniqueVehicleCounts = {
      car: new Set(),
      truck: new Set(),
      motorbikes: new Set(),
      other: new Set(),
    };
  }

  // Calculate Euclidean distance between two centroids
  distance(centroid1, centroid2) {
    return Math.sqrt(
      Math.pow(centroid1.x - centroid2.x, 2) +
        Math.pow(centroid1.y - centroid2.y, 2)
    );
  }

  // Check if bounding boxes are similar (based on size)
  isBboxSimilar(bbox1, bbox2) {
    const sizeThreshold = 0.6; // Allow 60% size difference
    const widthRatio =
      Math.abs(bbox1[2] - bbox2[2]) / Math.max(bbox1[2], bbox2[2]);
    const heightRatio =
      Math.abs(bbox1[3] - bbox2[3]) / Math.max(bbox1[3], bbox2[3]);
    return widthRatio < sizeThreshold && heightRatio < sizeThreshold;
  }

  // Predict next centroid based on last seen movement
  predictNextCentroid(vehicle) {
    if (!vehicle.lastCentroid) return vehicle.centroid;
    const dx = vehicle.centroid.x - vehicle.lastCentroid.x;
    const dy = vehicle.centroid.y - vehicle.lastCentroid.y;
    return {
      x: vehicle.centroid.x + dx,
      y: vehicle.centroid.y + dy,
    };
  }

  // Update tracker with new detections
  update(detections) {
    const newVehicles = new Map();
    const usedDetections = new Set();

    // Filter and map detections to only include vehicles
    const detectionCentroids = detections
      .filter((d) =>
        ["car", "truck", "motorcycle", "bus", "bicycle"].includes(d.class)
      )
      .map((d) => ({
        x: d.bbox[0] + d.bbox[2] / 2,
        y: d.bbox[1] + d.bbox[3] / 2,
        type: this.normalizeVehicleType(d.class),
        bbox: d.bbox,
        score: d.score,
      }));

    // Match existing vehicles to new detections
    for (const [id, vehicle] of this.vehicles) {
      let minDistance = Infinity;
      let closestIdx = -1;

      // Find closest detection to this vehicle
      detectionCentroids.forEach((det, idx) => {
        if (usedDetections.has(idx)) return;
        const predictedCentroid = this.predictNextCentroid(vehicle);
        const dist = this.distance(predictedCentroid, det);
        if (dist < minDistance && dist < 100 && det.type === vehicle.type) {
          minDistance = dist;
          closestIdx = idx;
        }
      });

      if (closestIdx !== -1) {
        // Update vehicle with new centroid and reset disappeared count
        newVehicles.set(id, {
          centroid: detectionCentroids[closestIdx],
          lastCentroid: vehicle.centroid,
          type: vehicle.type,
          disappeared: 0,
          bbox: detectionCentroids[closestIdx].bbox,
        });
        usedDetections.add(closestIdx);
      } else {
        // Increment disappeared count
        if (vehicle.disappeared < this.maxDisappeared) {
          newVehicles.set(id, {
            ...vehicle,
            disappeared: vehicle.disappeared + 1,
          });
        } else {
          // Move to disappeared vehicles
          this.disappearedVehicles.set(id, {
            ...vehicle,
            reidentifyFrames: 0,
          });
        }
      }
    }

    // Update disappeared vehicles
    const updatedDisappeared = new Map();
    for (const [id, vehicle] of this.disappearedVehicles) {
      if (vehicle.reidentifyFrames < this.maxReidentifyFrames) {
        updatedDisappeared.set(id, {
          ...vehicle,
          reidentifyFrames: vehicle.reidentifyFrames + 1,
        });
      }
    }
    this.disappearedVehicles = updatedDisappeared;

    // Add new detections as new or reidentified vehicles
    detectionCentroids.forEach((det, idx) => {
      if (usedDetections.has(idx)) return;

      // Try to reidentify with disappeared vehicles
      let reidentifiedId = null;
      let minDistance = Infinity;
      for (const [id, vehicle] of this.disappearedVehicles) {
        if (
          vehicle.type === det.type &&
          this.isBboxSimilar(vehicle.bbox, det.bbox)
        ) {
          const predictedCentroid = this.predictNextCentroid(vehicle);
          const dist = this.distance(predictedCentroid, det);
          if (dist < minDistance && dist < 200) {
            minDistance = dist;
            reidentifiedId = id;
          }
        }
      }

      if (reidentifiedId !== null) {
        // Reidentify vehicle
        newVehicles.set(reidentifiedId, {
          centroid: det,
          lastCentroid: this.disappearedVehicles.get(reidentifiedId).centroid,
          type: det.type,
          disappeared: 0,
          bbox: det.bbox,
        });
        this.disappearedVehicles.delete(reidentifiedId);
      } else {
        // New vehicle
        newVehicles.set(this.nextId, {
          centroid: det,
          lastCentroid: null,
          type: det.type,
          disappeared: 0,
          bbox: det.bbox,
        });
        // Add to unique vehicles set for this type
        this.uniqueVehicleCounts[det.type].add(this.nextId);
        this.totalUniqueVehicles++;
        this.nextId++;
      }
    });

    this.vehicles = newVehicles;
  }

  // Add new helper method to normalize vehicle types
  normalizeVehicleType(type) {
    switch (type) {
      case "car":
        return "car";
      case "truck":
      case "bus":
        return "truck";
      case "motorcycle":
      case "bicycle":
        return "motorbikes";
      default:
        return "other";
    }
  }

  // Replace getFrameCounts with getUniqueCounts
  getFrameCounts() {
    return {
      car: this.uniqueVehicleCounts.car.size,
      truck: this.uniqueVehicleCounts.truck.size,
      motorbikes: this.uniqueVehicleCounts.motorbikes.size,
      other: this.uniqueVehicleCounts.other.size,
    };
  }

  // Get total unique vehicles
  getTotalUniqueVehicles() {
    return this.totalUniqueVehicles;
  }
}

export default VehicleTracker;
