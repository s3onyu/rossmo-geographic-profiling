function manhattanDistance(lat1, lon1, lat2, lon2) {
    const latM = Math.abs(lat1 - lat2) * 111000;
    const lonM = Math.abs(lon1 - lon2) * 111000 * Math.cos((lat1 + lat2) / 2 * Math.PI / 180);
    return latM + lonM;
}

function haversineDistance(lat1, lon1, lat2, lon2) {
    const R = 6371000;
    const dLat = (lat2 - lat1) * Math.PI / 180;
    const dLon = (lon2 - lon1) * Math.PI / 180;
    const a = Math.sin(dLat/2)**2 + Math.cos(lat1*Math.PI/180)*Math.cos(lat2*Math.PI/180)*Math.sin(dLon/2)**2;
    return 2 * R * Math.asin(Math.sqrt(a));
}

function rossmoTerm(d, buffer, f, g, phi) {
    if (d <= 0) return 0;
    if (d > buffer) {
        return phi / Math.pow(d, f);
    } else {
        const denom = Math.pow(2 * buffer - d, g);
        if (denom === 0) return 0;
        return (1 - phi) * Math.pow(buffer, g - f) / denom;
    }
}

function computeRossmo(cells, crimes, distanceFn, buffer, f, g, priors) {
    const phi = 0.5;
    const probs = new Array(cells.length);
    let total = 0;
    
    for (let i = 0; i < cells.length; i++) {
        let likelihood = 0;
        for (let j = 0; j < crimes.length; j++) {
            const d = distanceFn(i, j);
            likelihood += rossmoTerm(d, buffer, f, g, phi);
        }
        const prior = priors ? priors[i] : 1;
        probs[i] = likelihood * prior;
        total += probs[i];
    }
    
    if (total > 0) {
        for (let i = 0; i < probs.length; i++) probs[i] /= total;
    }
    
    return probs;
}

function computeRisk(cells, offenders, buffer, f, g) {
    const activityRadius = buffer * 3;
    const risks = new Array(cells.length).fill(0);
    let maxRisk = 0;
    
    for (let i = 0; i < cells.length; i++) {
        const cell = cells[i];
        let risk = 0;
        
        for (let j = 0; j < offenders.length; j++) {
            const off = offenders[j];
            const d = manhattanDistance(cell.lat, cell.lon, off.lat, off.lon);
            
            if (d > activityRadius) continue;
            
            if (d < buffer * 0.3) {
                risk += 0.3;
            } else if (d < buffer) {
                risk += 1.0;
            } else {
                const decay = 1.0 - (d - buffer) / (activityRadius - buffer);
                risk += decay * 0.8;
            }
        }
        
        risks[i] = risk;
        if (risk > maxRisk) maxRisk = risk;
    }
    
    if (maxRisk > 0) {
        for (let i = 0; i < risks.length; i++) risks[i] /= maxRisk;
    }
    
    return risks;
}

function findMaxCell(probs, cells) {
    let maxP = -1, maxIdx = 0;
    for (let i = 0; i < probs.length; i++) {
        if (probs[i] > maxP) {
            maxP = probs[i];
            maxIdx = i;
        }
    }
    return { cell: cells[maxIdx], prob: maxP, idx: maxIdx };
}function computeSafetyScores(cells, offenders, safetyFeatures, buffer) {
    const scores = new Array(cells.length).fill(0);
    
    for (let i = 0; i < cells.length; i++) {
        const cell = cells[i];
        let risk = 0;
        let safety = 0;
        
        for (const off of offenders) {
            const d = manhattanDistance(cell.lat, cell.lon, off.lat, off.lon);
            if (d < buffer * 3) {
                risk += Math.exp(-d / buffer);
            }
        }
        
        if (safetyFeatures) {
            for (const f of safetyFeatures) {
                const d = manhattanDistance(cell.lat, cell.lon, f.lat, f.lon);
                if (d < 300) {
                    if (f.type === 'convenience') safety += 0.5 * Math.exp(-d / 150);
                    else if (f.type === 'police') safety += 0.8 * Math.exp(-d / 200);
                    else if (f.type === 'fuel') safety += 0.3 * Math.exp(-d / 150);
                    else if (f.type === 'lamp') safety += 0.2 * Math.exp(-d / 100);
                }
            }
        }
        
        scores[i] = risk - safety;
    }
    
    return scores;
}

function findPath(cells, rows, cols, startIdx, endIdx, safetyScores, safetyWeight) {
    const n = cells.length;
    const dist = new Array(n).fill(Infinity);
    const prev = new Array(n).fill(-1);
    const visited = new Array(n).fill(false);
    dist[startIdx] = 0;
    
    const heap = [[0, startIdx]];
    
    while (heap.length > 0) {
        heap.sort((a, b) => a[0] - b[0]);
        const [d, u] = heap.shift();
        
        if (visited[u]) continue;
        visited[u] = true;
        
        if (u === endIdx) break;
        
        const row = Math.floor(u / cols);
        const col = u % cols;
        
        for (const [dr, dc] of [[-1,0],[1,0],[0,-1],[0,1],[-1,-1],[-1,1],[1,-1],[1,1]]) {
            const nr = row + dr;
            const nc = col + dc;
            if (nr < 0 || nr >= rows || nc < 0 || nc >= cols) continue;
            
            const v = nr * cols + nc;
            const cell1 = cells[u];
            const cell2 = cells[v];
            const stepDist = haversineDistance(cell1.lat, cell1.lon, cell2.lat, cell2.lon);
            
            const dangerFactor = 1 + safetyWeight * Math.max(0, safetyScores[v]) * 5;
            const cost = stepDist * dangerFactor;
            
            if (dist[u] + cost < dist[v]) {
                dist[v] = dist[u] + cost;
                prev[v] = u;
                heap.push([dist[v], v]);
            }
        }
    }
    
    const path = [];
    let cur = endIdx;
    while (cur !== -1) {
        path.push(cur);
        cur = prev[cur];
    }
    path.reverse();
    
    let totalDist = 0;
    for (let i = 1; i < path.length; i++) {
        const c1 = cells[path[i-1]];
        const c2 = cells[path[i]];
        totalDist += haversineDistance(c1.lat, c1.lon, c2.lat, c2.lon);
    }
    
    return { path, distance: totalDist };
}

function findNearestCell(cells, lat, lon) {
    let minDist = Infinity;
    let minIdx = 0;
    for (let i = 0; i < cells.length; i++) {
        const d = haversineDistance(cells[i].lat, cells[i].lon, lat, lon);
        if (d < minDist) {
            minDist = d;
            minIdx = i;
        }
    }
    return minIdx;
}