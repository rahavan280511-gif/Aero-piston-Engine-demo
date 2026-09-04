import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

// ---------------------------------------------------------------------------
// Scene, Camera, Renderer & Studio Lighting Setup
// ---------------------------------------------------------------------------
const scene = new THREE.Scene();
scene.background = new THREE.Color(0x0f1117);

const camera = new THREE.PerspectiveCamera(
    45,
    window.innerWidth / window.innerHeight,
    0.1,
    1000
);
camera.position.set(4.5, 3.2, 4.5);

const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
renderer.setSize(window.innerWidth, window.innerHeight);
renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
renderer.shadowMap.enabled = true;
renderer.shadowMap.type = THREE.PCFSoftShadowMap;
document.body.appendChild(renderer.domElement);

// Orbit Controls for interactive 360° inspection
let controls;
try {
    controls = new OrbitControls(camera, renderer.domElement);
    controls.target.set(0, 0.95, 0);
    controls.enableDamping = true;
    controls.dampingFactor = 0.05;
    controls.maxPolarAngle = Math.PI / 2 + 0.1;
} catch (e) {
    console.warn("OrbitControls fallback:", e);
}

// Studio Lighting Setup
const ambientLight = new THREE.AmbientLight(0xffffff, 0.85);
scene.add(ambientLight);

const keyLight = new THREE.DirectionalLight(0xffffff, 1.6);
keyLight.position.set(5, 9, 6);
keyLight.castShadow = true;
scene.add(keyLight);

const fillLight = new THREE.DirectionalLight(0x3366ff, 0.5);
fillLight.position.set(-5, 4, -4);
scene.add(fillLight);

const rimLight = new THREE.DirectionalLight(0xffaa44, 0.7);
rimLight.position.set(0, 6, -6);
scene.add(rimLight);

// Ground Grid Floor
const gridHelper = new THREE.GridHelper(12, 24, 0x00d2ff, 0x1e293b);
gridHelper.position.y = -0.01;
scene.add(gridHelper);

// ---------------------------------------------------------------------------
// Helper for Z-Axis Aligned Cylinders (Pre-rotated geometry to avoid Euler wobble)
// ---------------------------------------------------------------------------
function createZCylinder(radiusTop, radiusBottom, height, radialSegments, material) {
    const geo = new THREE.CylinderGeometry(radiusTop, radiusBottom, height, radialSegments);
    geo.rotateX(Math.PI / 2); // Align cylinder centerline along Z-axis permanently
    return new THREE.Mesh(geo, material);
}

function createZCone(radius, height, radialSegments, material) {
    const geo = new THREE.ConeGeometry(radius, height, radialSegments);
    geo.rotateX(Math.PI / 2); // Align cone centerline along Z-axis permanently
    return new THREE.Mesh(geo, material);
}

function createZTorus(radius, tube, radialSegments, tubularSegments, material) {
    const geo = new THREE.TorusGeometry(radius, tube, radialSegments, tubularSegments);
    // Torus default plane is XY (facing Z). No rotation needed.
    return new THREE.Mesh(geo, material);
}

// ---------------------------------------------------------------------------
// Materials Definition
// ---------------------------------------------------------------------------

// 1. Engine Block / Crankcase Material (Silver -> Amber -> Red based on Health/Faults)
const blockMaterial = new THREE.MeshStandardMaterial({
    color: 0xd0d8e0,     // Metallic Silver
    metalness: 0.85,
    roughness: 0.25,
});

// 2. High-Gloss Polished Chrome (Supercharger Case, Air Scoop, Snout)
const chromeMaterial = new THREE.MeshStandardMaterial({
    color: 0xf8fafc,     // Brilliant Polished Chrome
    metalness: 0.95,
    roughness: 0.06,
});

// 3. Iconic Anodized Red Butterfly Valve Material (Dom Toretto Bugcatcher Scoop)
const butterflyRedMaterial = new THREE.MeshStandardMaterial({
    color: 0xef4444,     // Anodized Crimson Red
    metalness: 0.8,
    roughness: 0.2,
    emissive: 0x440000,
    emissiveIntensity: 0.2,
});

// 4. Machined Aluminum Parts (Pulleys, Flanges, Linkages)
const aluminumMaterial = new THREE.MeshStandardMaterial({
    color: 0xb8c6d4,
    metalness: 0.8,
    roughness: 0.3,
});

// 5. Dark Cast Iron / Steel Parts
const darkMetalMaterial = new THREE.MeshStandardMaterial({
    color: 0x22252a,
    metalness: 0.75,
    roughness: 0.45,
});

// 6. Cogged Rubber Blower Drive Belt
const beltMaterial = new THREE.MeshStandardMaterial({
    color: 0x18181b,
    metalness: 0.2,
    roughness: 0.8,
});

// 7. Red Ignition / Fuel Lines
const redWireMaterial = new THREE.MeshStandardMaterial({
    color: 0xd32f2f,
    metalness: 0.3,
    roughness: 0.5,
});

// 8. Cylinder Head / Cooling Fins Thermal Material (Green -> Yellow -> Red via CHT)
const chtMaterial = new THREE.MeshStandardMaterial({
    color: 0x00e676,     // Cool Green
    metalness: 0.55,
    roughness: 0.35,
    emissive: 0x003311,
    emissiveIntensity: 0.2,
});

// 9. Exhaust System Thermal Material (Green -> Yellow -> Red via EGT)
const egtMaterial = new THREE.MeshStandardMaterial({
    color: 0x00e676,     // Cool Green
    metalness: 0.65,
    roughness: 0.3,
    emissive: 0x003311,
    emissiveIntensity: 0.25,
});

// 10. Valve Cover Material (Ribbed Anodized Dark Metal)
const valveCoverMaterial = new THREE.MeshStandardMaterial({
    color: 0x27272a,
    metalness: 0.8,
    roughness: 0.3,
});

// 11. Oil Pan Sump Material
const oilPanMaterial = new THREE.MeshStandardMaterial({
    color: 0x1f242d,
    metalness: 0.8,
    roughness: 0.35,
});

// 12. Propeller & Spinner Materials
const propBladeMaterial = new THREE.MeshStandardMaterial({
    color: 0x111111,
    metalness: 0.4,
    roughness: 0.5,
});

const spinnerMaterial = new THREE.MeshStandardMaterial({
    color: 0xe2e8f0,
    metalness: 0.9,
    roughness: 0.15,
});

// 13. Spark Plug & Fitting Details
const sparkPlugMaterial = new THREE.MeshStandardMaterial({
    color: 0xf8fafc,
    roughness: 0.1,
});

const brassMaterial = new THREE.MeshStandardMaterial({
    color: 0xd4af37,
    metalness: 0.85,
    roughness: 0.25,
});

// ---------------------------------------------------------------------------
// V8 Aero-Engine Master Group
// ---------------------------------------------------------------------------
const engineGroup = new THREE.Group();
scene.add(engineGroup);

// ---------------------------------------------------------------------------
// 1. V8 Engine Block & Crankcase Architecture
// ---------------------------------------------------------------------------
const crankcaseGroup = new THREE.Group();
engineGroup.add(crankcaseGroup);

// Main V8 Crankcase Base
const crankcaseBase = new THREE.Mesh(
    new THREE.BoxGeometry(0.9, 0.55, 1.7),
    blockMaterial
);
crankcaseBase.position.set(0, 0.35, 0);
crankcaseGroup.add(crankcaseBase);

// Bottom Crank Trench
const crankTrench = createZCylinder(0.45, 0.45, 1.7, 32, blockMaterial);
crankTrench.position.set(0, 0.2, 0);
crankcaseGroup.add(crankTrench);

// Deep Oil Pan Sump
const oilPan = new THREE.Mesh(
    new THREE.BoxGeometry(0.8, 0.25, 1.3),
    oilPanMaterial
);
oilPan.position.set(0, 0.05, -0.1);
crankcaseGroup.add(oilPan);

// Oil Drain Plug
const drainPlug = new THREE.Mesh(
    new THREE.CylinderGeometry(0.04, 0.04, 0.05, 12),
    brassMaterial
);
drainPlug.position.set(0, -0.075, -0.5);
crankcaseGroup.add(drainPlug);

// Front Timing Cover
const timingCover = new THREE.Mesh(
    new THREE.BoxGeometry(0.85, 0.65, 0.12),
    blockMaterial
);
timingCover.position.set(0, 0.45, 0.9);
crankcaseGroup.add(timingCover);

// Rear Flywheel Housing
const flywheelHousing = createZCylinder(0.55, 0.55, 0.15, 32, darkMetalMaterial);
flywheelHousing.position.set(0, 0.45, -0.92);
crankcaseGroup.add(flywheelHousing);

// ---------------------------------------------------------------------------
// 2. Dual Cylinder Banks (90° V8 Layout — 4 Cylinders Per Bank)
// ---------------------------------------------------------------------------
const pistons = [];
const conRods = [];
const cylinderSpacing = 0.38;
const startZ = 0.57;
const bankAngle = Math.PI / 4; // 45° from vertical (90° V angle)

const leftBankGroup = new THREE.Group();
leftBankGroup.position.set(-0.25, 0.55, 0);
leftBankGroup.rotation.z = bankAngle;
engineGroup.add(leftBankGroup);

const rightBankGroup = new THREE.Group();
rightBankGroup.position.set(0.25, 0.55, 0);
rightBankGroup.rotation.z = -bankAngle;
engineGroup.add(rightBankGroup);

function buildCylinderBank(bankGroup, isLeft) {
    for (let i = 0; i < 4; i++) {
        const zPos = startZ - i * cylinderSpacing;
        const cylGroup = new THREE.Group();
        cylGroup.position.set(0, 0, zPos);
        bankGroup.add(cylGroup);

        // Cylinder Sleeve Barrel
        const sleeve = new THREE.Mesh(
            new THREE.CylinderGeometry(0.22, 0.22, 0.65, 32),
            darkMetalMaterial
        );
        sleeve.position.set(0, 0.325, 0);
        cylGroup.add(sleeve);

        // 7 Cooling Fins per cylinder (using CHT thermal material)
        for (let f = 0; f < 7; f++) {
            const finMesh = new THREE.Mesh(
                new THREE.CylinderGeometry(0.31 - f * 0.005, 0.31 - f * 0.005, 0.018, 32),
                chtMaterial
            );
            finMesh.position.set(0, 0.12 + f * 0.065, 0);
            cylGroup.add(finMesh);
        }

        // Cylinder Head Block
        const headBlock = new THREE.Mesh(
            new THREE.CylinderGeometry(0.3, 0.3, 0.14, 32),
            chtMaterial
        );
        headBlock.position.set(0, 0.68, 0);
        cylGroup.add(headBlock);

        // Head Bolts
        for (let bx of [-0.18, 0.18]) {
            for (let bz of [-0.18, 0.18]) {
                const bolt = new THREE.Mesh(
                    new THREE.CylinderGeometry(0.025, 0.025, 0.06, 6),
                    aluminumMaterial
                );
                bolt.position.set(bx, 0.75, bz);
                cylGroup.add(bolt);
            }
        }

        // Dual Spark Plugs
        for (let spAngle of [-0.2, 0.2]) {
            const plugHex = new THREE.Mesh(
                new THREE.CylinderGeometry(0.035, 0.035, 0.06, 6),
                brassMaterial
            );
            plugHex.position.set(spAngle, 0.77, 0);
            cylGroup.add(plugHex);

            const plugCeramic = new THREE.Mesh(
                new THREE.CylinderGeometry(0.02, 0.022, 0.08, 12),
                sparkPlugMaterial
            );
            plugCeramic.position.set(spAngle, 0.83, 0);
            cylGroup.add(plugCeramic);
        }

        // Internal Kinematics: Piston & Connecting Rod
        const piston = new THREE.Mesh(
            new THREE.CylinderGeometry(0.205, 0.205, 0.2, 24),
            new THREE.MeshStandardMaterial({ color: 0xd1d5db, metalness: 0.9, roughness: 0.15 })
        );
        piston.position.set(0, 0.35, 0);
        cylGroup.add(piston);

        const conRod = new THREE.Mesh(
            new THREE.CylinderGeometry(0.022, 0.022, 0.38, 16),
            aluminumMaterial
        );
        conRod.position.set(0, 0.12, 0);
        cylGroup.add(conRod);

        // Phase offsets (V8 firing order 1-8-4-3-6-5-7-2)
        const cylIdx = isLeft ? i : i + 4;
        const phaseOffsets = [0, Math.PI / 2, Math.PI, (3 * Math.PI) / 2, Math.PI / 4, (3 * Math.PI) / 4, (5 * Math.PI) / 4, (7 * Math.PI) / 4];
        pistons.push({ mesh: piston, phase: phaseOffsets[cylIdx] });
        conRods.push({ mesh: conRod, phase: phaseOffsets[cylIdx] });
    }
}

buildCylinderBank(leftBankGroup, true);
buildCylinderBank(rightBankGroup, false);

// ---------------------------------------------------------------------------
// 3. Ribbed Dark Metal Valve Covers & Red Wires
// ---------------------------------------------------------------------------
const leftValveCover = new THREE.Mesh(
    new THREE.BoxGeometry(0.48, 0.18, 1.6),
    valveCoverMaterial
);
leftValveCover.position.set(0, 0.82, -0.05);
leftBankGroup.add(leftValveCover);

const rightValveCover = new THREE.Mesh(
    new THREE.BoxGeometry(0.48, 0.18, 1.6),
    valveCoverMaterial
);
rightValveCover.position.set(0, 0.82, -0.05);
rightBankGroup.add(rightValveCover);

// Chrome Oil Cap
const oilCap = new THREE.Mesh(
    new THREE.CylinderGeometry(0.08, 0.08, 0.06, 16),
    chromeMaterial
);
oilCap.position.set(0, 0.94, 0.4);
leftBankGroup.add(oilCap);

// Red Ignition Wires
for (let i = 0; i < 4; i++) {
    const zPos = startZ - i * cylinderSpacing;
    const wireL = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.35, 8), redWireMaterial);
    wireL.position.set(-0.22, 0.88, zPos);
    leftBankGroup.add(wireL);

    const wireR = new THREE.Mesh(new THREE.CylinderGeometry(0.012, 0.012, 0.35, 8), redWireMaterial);
    wireR.position.set(0.22, 0.88, zPos);
    rightBankGroup.add(wireR);
}

// ---------------------------------------------------------------------------
// 4. Dom Toretto 6-71 Blower, Dual Carburetors & 3-Hole Stadium Air Scoop
// ---------------------------------------------------------------------------
const superchargerGroup = new THREE.Group();
superchargerGroup.position.set(0, 0.82, -0.05);
engineGroup.add(superchargerGroup);

// A. Lower Blower Intake Manifold Base
const blowerManifold = new THREE.Mesh(
    new THREE.BoxGeometry(0.44, 0.1, 1.45),
    aluminumMaterial
);
blowerManifold.position.set(0, 0.05, 0);
superchargerGroup.add(blowerManifold);

// 8 Intake Runners
for (let i = 0; i < 4; i++) {
    const zPos = startZ - i * cylinderSpacing - 0.05;
    const lRun = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.22, 16), aluminumMaterial);
    lRun.rotation.z = Math.PI / 3.5;
    lRun.position.set(-0.2, 0.02, zPos);
    superchargerGroup.add(lRun);

    const rRun = new THREE.Mesh(new THREE.CylinderGeometry(0.04, 0.04, 0.22, 16), aluminumMaterial);
    rRun.rotation.z = -Math.PI / 3.5;
    rRun.position.set(0.2, 0.02, zPos);
    superchargerGroup.add(rRun);
}

// B. 6-71 Roots Supercharger Main Chrome Housing
const blowerCase = new THREE.Mesh(
    new THREE.BoxGeometry(0.48, 0.36, 1.25),
    chromeMaterial
);
blowerCase.position.set(0, 0.28, 0);
superchargerGroup.add(blowerCase);

// Double Rotor Humps
for (let side of [-0.12, 0.12]) {
    const rotorHump = createZCylinder(0.14, 0.14, 1.25, 24, chromeMaterial);
    rotorHump.position.set(side, 0.45, 0);
    superchargerGroup.add(rotorHump);
}

// Side Cooling Ribs
for (let rib = 0; rib < 5; rib++) {
    const yRib = 0.15 + rib * 0.06;
    const sideRibL = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.02, 1.2), aluminumMaterial);
    sideRibL.position.set(-0.25, yRib, 0);
    superchargerGroup.add(sideRibL);

    const sideRibR = new THREE.Mesh(new THREE.BoxGeometry(0.03, 0.02, 1.2), aluminumMaterial);
    sideRibR.position.set(0.25, yRib, 0);
    superchargerGroup.add(sideRibR);
}

// C. Long Cylindrical Blower Snout
const blowerFrontPlate = new THREE.Mesh(
    new THREE.BoxGeometry(0.5, 0.38, 0.06),
    chromeMaterial
);
blowerFrontPlate.position.set(0, 0.28, 0.65);
superchargerGroup.add(blowerFrontPlate);

const blowerSnout = createZCylinder(0.09, 0.09, 0.42, 24, chromeMaterial);
blowerSnout.position.set(0, 0.28, 0.88);
superchargerGroup.add(blowerSnout);

// D. Top Blower Cogged Pulley (Z-Axis Pre-Rotated)
const blowerPulley = createZCylinder(0.24, 0.24, 0.12, 32, aluminumMaterial);
blowerPulley.position.set(0, 0.28, 1.08);
superchargerGroup.add(blowerPulley);

const blowerFlange = createZCylinder(0.26, 0.26, 0.02, 32, chromeMaterial);
blowerFlange.position.set(0, 0.28, 1.14);
superchargerGroup.add(blowerFlange);

// E. Dual Carburetors & Fuel Rail
for (let carbZ of [-0.25, 0.25]) {
    const carbBlock = new THREE.Mesh(
        new THREE.BoxGeometry(0.36, 0.14, 0.36),
        aluminumMaterial
    );
    carbBlock.position.set(0, 0.52, carbZ);
    superchargerGroup.add(carbBlock);

    const fuelReg = new THREE.Mesh(
        new THREE.CylinderGeometry(0.04, 0.04, 0.12, 16),
        chromeMaterial
    );
    fuelReg.rotation.z = Math.PI / 2;
    fuelReg.position.set(-0.22, 0.52, carbZ);
    superchargerGroup.add(fuelReg);
}

// ---------------------------------------------------------------------------
// F. STADIUM-SHAPED AIR SCOOP WITH 3 CIRCULAR BORE HOLES (EXACT ENDERLE BUGCATCHER MATCH)
// ---------------------------------------------------------------------------
const scoopGroup = new THREE.Group();
scoopGroup.position.set(0, 0.62, 0);
superchargerGroup.add(scoopGroup);

// 1. Base Plate
const scoopAdapter = new THREE.Mesh(
    new THREE.BoxGeometry(0.44, 0.06, 0.85),
    chromeMaterial
);
scoopAdapter.position.set(0, 0.03, 0);
scoopGroup.add(scoopAdapter);

// 2. Main Stadium / Capsule Scoop Housing (Rectangle with Semicircular Rounded Sides)
// Central Rectangular Section
const scoopCenterRect = new THREE.Mesh(
    new THREE.BoxGeometry(0.38, 0.28, 0.95),
    chromeMaterial
);
scoopCenterRect.position.set(0, 0.20, 0.05);
scoopGroup.add(scoopCenterRect);

// Left Semicircular Curved Side Wall
const scoopSideL = createZCylinder(0.14, 0.14, 0.95, 32, chromeMaterial);
scoopSideL.position.set(-0.19, 0.20, 0.05);
scoopGroup.add(scoopSideL);

// Right Semicircular Curved Side Wall
const scoopSideR = createZCylinder(0.14, 0.14, 0.95, 32, chromeMaterial);
scoopSideR.position.set(0.19, 0.20, 0.05);
scoopGroup.add(scoopSideR);

// 3. Front Faceplate with 3 DISTINCT CIRCULAR BORE HOLES (Reference Match!)
const frontFaceplate = new THREE.Mesh(
    new THREE.BoxGeometry(0.64, 0.32, 0.04),
    chromeMaterial
);
frontFaceplate.position.set(0, 0.20, 0.54);
scoopGroup.add(frontFaceplate);

// 3 Heavy Chrome Circular Bezel Rings (Creating the 3 Distinct Front Bore Holes!)
const butterflyPlates = [];

for (let b = 0; b < 3; b++) {
    const xPos = -0.17 + b * 0.17;
    
    // Outer Chrome Ring Bezel around each circular hole
    const holeBezel = createZTorus(0.088, 0.016, 16, 32, chromeMaterial);
    holeBezel.position.set(xPos, 0.20, 0.56);
    scoopGroup.add(holeBezel);

    // Dark Recessed Interior Hole Cavity
    const holeCavity = createZCylinder(0.082, 0.082, 0.05, 32, darkMetalMaterial);
    holeCavity.position.set(xPos, 0.20, 0.53);
    scoopGroup.add(holeCavity);

    // Red Circular Butterfly Valve Plate inside each hole!
    const butterflyGroup = new THREE.Group();
    butterflyGroup.position.set(xPos, 0.20, 0.55);
    scoopGroup.add(butterflyGroup);

    // Pre-rotated Z-disc plate
    const plateGeo = new THREE.CylinderGeometry(0.076, 0.076, 0.008, 24);
    plateGeo.rotateX(Math.PI / 2); // Flat face facing forward (Z)
    const plate = new THREE.Mesh(plateGeo, butterflyRedMaterial);
    butterflyGroup.add(plate);

    butterflyPlates.push(butterflyGroup);
}

// 4. Side Throttle Linkage Rod & Bracket (Right Side)
const sideLinkageLever = new THREE.Mesh(
    new THREE.BoxGeometry(0.02, 0.25, 0.03),
    aluminumMaterial
);
sideLinkageLever.position.set(0.31, 0.18, 0.52);
scoopGroup.add(sideLinkageLever);

const sideLinkageRod = new THREE.Mesh(
    new THREE.CylinderGeometry(0.008, 0.008, 0.6, 8),
    chromeMaterial
);
sideLinkageRod.rotation.x = Math.PI / 3;
sideLinkageRod.position.set(0.31, -0.05, 0.3);
scoopGroup.add(sideLinkageRod);

// ---------------------------------------------------------------------------
// 5. CONNECTED SUPERCHARGER DRIVE BELT & PULLEYS (PRE-ROTATED ZERO-WOBBLE)
// ---------------------------------------------------------------------------
const beltDriveGroup = new THREE.Group();
beltDriveGroup.position.set(0, 0, 1.08); // Z = 1.08 directly aligned with top snout pulley!
engineGroup.add(beltDriveGroup);

// Bottom Crankshaft Blower Pulley (Z-Axis Pre-Rotated)
const crankBlowerPulley = createZCylinder(0.24, 0.24, 0.12, 32, aluminumMaterial);
crankBlowerPulley.position.set(0, 0.45, 0);
beltDriveGroup.add(crankBlowerPulley);

const crankBlowerFlange = createZCylinder(0.26, 0.26, 0.02, 32, chromeMaterial);
crankBlowerFlange.position.set(0, 0.45, 0.06);
beltDriveGroup.add(crankBlowerFlange);

// Side Belt Tensioner / Idler Arm & Pulley (Z-Axis Pre-Rotated)
const tensionerArm = new THREE.Mesh(
    new THREE.BoxGeometry(0.25, 0.06, 0.04),
    aluminumMaterial
);
tensionerArm.position.set(-0.22, 0.72, -0.04);
beltDriveGroup.add(tensionerArm);

const tensionerPulley = createZCylinder(0.12, 0.12, 0.12, 24, chromeMaterial);
tensionerPulley.position.set(-0.32, 0.72, 0);
beltDriveGroup.add(tensionerPulley);

// Continuous Wide Black Cogged Belt
const beltRight = new THREE.Mesh(
    new THREE.BoxGeometry(0.12, 0.65, 0.05),
    beltMaterial
);
beltRight.position.set(0.24, 0.775, 0);
beltDriveGroup.add(beltRight);

const beltLeftLower = new THREE.Mesh(
    new THREE.BoxGeometry(0.12, 0.32, 0.05),
    beltMaterial
);
beltLeftLower.rotation.z = Math.PI / 8;
beltLeftLower.position.set(-0.28, 0.58, 0);
beltDriveGroup.add(beltLeftLower);

const beltLeftUpper = new THREE.Mesh(
    new THREE.BoxGeometry(0.12, 0.42, 0.05),
    beltMaterial
);
beltLeftUpper.rotation.z = -Math.PI / 9;
beltLeftUpper.position.set(-0.26, 0.92, 0);
beltDriveGroup.add(beltLeftUpper);

// ---------------------------------------------------------------------------
// 6. Dual 4-into-1 Exhaust Headers & Crossover Muffler System (EGT Channel)
// ---------------------------------------------------------------------------
const exhaustGroup = new THREE.Group();
engineGroup.add(exhaustGroup);

for (let i = 0; i < 4; i++) {
    const zPos = startZ - i * cylinderSpacing;
    
    const leftPipe = new THREE.Mesh(
        new THREE.CylinderGeometry(0.05, 0.05, 0.45, 16),
        egtMaterial
    );
    leftPipe.rotation.z = -Math.PI / 2.8;
    leftPipe.position.set(-0.62, 0.72, zPos);
    exhaustGroup.add(leftPipe);

    const rightPipe = new THREE.Mesh(
        new THREE.CylinderGeometry(0.05, 0.05, 0.45, 16),
        egtMaterial
    );
    rightPipe.rotation.z = Math.PI / 2.8;
    rightPipe.position.set(0.62, 0.72, zPos);
    exhaustGroup.add(rightPipe);
}

// Collector Pipes
const leftCollector = new THREE.Mesh(
    new THREE.CylinderGeometry(0.09, 0.09, 1.5, 24),
    egtMaterial
);
leftCollector.position.set(-0.78, 0.52, -0.05);
exhaustGroup.add(leftCollector);

const rightCollector = new THREE.Mesh(
    new THREE.CylinderGeometry(0.09, 0.09, 1.5, 24),
    egtMaterial
);
rightCollector.position.set(0.78, 0.52, -0.05);
exhaustGroup.add(rightCollector);

// H-Pipe Crossover
const hPipe = new THREE.Mesh(
    new THREE.CylinderGeometry(0.07, 0.07, 1.45, 16),
    egtMaterial
);
hPipe.rotation.z = Math.PI / 2;
hPipe.position.set(0, 0.48, -0.4);
exhaustGroup.add(hPipe);

// Mufflers & Tips
const leftMuffler = new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.15, 0.6, 24), egtMaterial);
leftMuffler.position.set(-0.78, 0.52, -1.05);
exhaustGroup.add(leftMuffler);

const rightMuffler = new THREE.Mesh(new THREE.CylinderGeometry(0.15, 0.15, 0.6, 24), egtMaterial);
rightMuffler.position.set(0.78, 0.52, -1.05);
exhaustGroup.add(rightMuffler);

const leftTip = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.25, 16), aluminumMaterial);
leftTip.position.set(-0.78, 0.52, -1.42);
exhaustGroup.add(leftTip);

const rightTip = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.25, 16), aluminumMaterial);
rightTip.position.set(0.78, 0.52, -1.42);
exhaustGroup.add(rightTip);

// ---------------------------------------------------------------------------
// 7. Front Accessory Drive & Serpentine Belt Pulleys (Pre-Rotated Z-Cylinders)
// ---------------------------------------------------------------------------
const frontDriveGroup = new THREE.Group();
frontDriveGroup.position.set(0, 0.45, 0.96);
engineGroup.add(frontDriveGroup);

const altPulley = createZCylinder(0.12, 0.12, 0.06, 24, aluminumMaterial);
altPulley.position.set(-0.35, 0.38, 0);
frontDriveGroup.add(altPulley);

const wpPulley = createZCylinder(0.16, 0.16, 0.06, 24, aluminumMaterial);
wpPulley.position.set(0, 0.45, 0);
frontDriveGroup.add(wpPulley);

const serptTensioner = createZCylinder(0.1, 0.1, 0.05, 24, aluminumMaterial);
serptTensioner.position.set(0.36, 0.2, 0);
frontDriveGroup.add(serptTensioner);

// ---------------------------------------------------------------------------
// 8. Aero Propeller Assembly (Positioned Forward at Z = 1.45)
// ---------------------------------------------------------------------------
const propGroup = new THREE.Group();
propGroup.position.set(0, 0.45, 1.45);
engineGroup.add(propGroup);

const propShaft = createZCylinder(0.07, 0.07, 0.45, 24, darkMetalMaterial);
propShaft.position.set(0, 0, -0.25);
propGroup.add(propShaft);

const spinnerCone = createZCone(0.28, 0.45, 32, spinnerMaterial);
spinnerCone.position.set(0, 0, 0.2);
propGroup.add(spinnerCone);

const hubPlate = createZCylinder(0.26, 0.26, 0.08, 32, aluminumMaterial);
hubPlate.position.set(0, 0, 0);
propGroup.add(hubPlate);

// 3 Aero Carbon Blades
const bladeGeo = new THREE.BoxGeometry(1.7, 0.04, 0.15);
for (let b = 0; b < 3; b++) {
    const bladeHolder = new THREE.Group();
    bladeHolder.rotation.z = (b * 2 * Math.PI) / 3;
    propGroup.add(bladeHolder);

    const bladeMesh = new THREE.Mesh(bladeGeo, propBladeMaterial);
    bladeMesh.position.set(0.8, 0, 0);
    bladeHolder.add(bladeMesh);

    const tipGeo = new THREE.BoxGeometry(0.18, 0.042, 0.152);
    const tipMat = new THREE.MeshBasicMaterial({ color: 0xffeb3b });
    const tipMesh = new THREE.Mesh(tipGeo, tipMat);
    tipMesh.position.set(1.58, 0, 0);
    bladeHolder.add(tipMesh);
}

// ---------------------------------------------------------------------------
// Dynamic Telemetry Color Mapping & Dynamics Helpers
// ---------------------------------------------------------------------------
let rpm = 2400;
let throttleVal = 0.6;
let propAngle = 0;
let crankAngle = 0;
let currentButterflyAngle = 0;
let targetButterflyAngle = 0;

function tempToColor(val, minTemp, maxTemp) {
    const t = Math.max(0, Math.min(1, (val - minTemp) / (maxTemp - minTemp)));
    let r, g, b;
    if (t < 0.5) {
        const f = t * 2;
        r = Math.floor(255 * f);
        g = 230 + Math.floor(5 * f);
        b = Math.floor(118 * (1 - f));
    } else {
        const f = (t - 0.5) * 2;
        r = 255;
        g = Math.floor(235 * (1 - f));
        b = Math.floor(59 * (1 - f));
    }
    return new THREE.Color(r / 255, g / 255, b / 255);
}

function updateEngineState(data) {
    if (typeof data.rpm === "number") {
        rpm = data.rpm;
    }
    if (typeof data.throttle === "number") {
        throttleVal = data.throttle;
        // Map throttle [0.20, 0.95] -> Butterfly tilt angle [5° (0.08 rad) to 75° (1.3 rad)]
        const normThr = Math.max(0, Math.min(1, (throttleVal - 0.20) / 0.75));
        targetButterflyAngle = 0.08 + normThr * 1.22;
    }

    // CHT Thermal Color Sync
    if (typeof data.cht === "number") {
        const c = tempToColor(data.cht, 140, 220);
        chtMaterial.color.copy(c);
        chtMaterial.emissive.copy(c).multiplyScalar(0.25);
    }

    // EGT Thermal Color Sync
    if (typeof data.egt === "number") {
        const c = tempToColor(data.egt, 550, 830);
        egtMaterial.color.copy(c);
        egtMaterial.emissive.copy(c).multiplyScalar(0.3);
    }

    // Oil Thermal Color Sync
    if (typeof data.oil_temp === "number") {
        const cOil = tempToColor(data.oil_temp, 70, 120);
        oilPanMaterial.color.copy(cOil).multiplyScalar(0.5);
    }

    // Engine Block Health Color
    const health = typeof data.health === "number" ? data.health : 100;
    const faultSuggestion = data.fault_suggestion || "NOMINAL";
    const anomalyActive = data.anomaly === true;

    if (anomalyActive && (faultSuggestion === "POSSIBLE_OVERHEATING" || health < 55)) {
        blockMaterial.color.setHex(0xd32f2f);
    } else if (anomalyActive && (faultSuggestion === "OIL_SYSTEM_CONCERN" || health < 70)) {
        blockMaterial.color.setHex(0xff9800);
    } else {
        blockMaterial.color.setHex(0xd0d8e0);
    }

    // Background Anomaly Warning Alarm Flash
    if (typeof data.anomaly === "boolean" && data.anomaly) {
        const time = Date.now() * 0.005;
        const intensity = (Math.sin(time) + 1) * 0.5;
        const flash = new THREE.Color().setHSL(0, 0.8, 0.08 + 0.06 * intensity);
        scene.background = flash;
    } else {
        scene.background = new THREE.Color(0x0f1117);
    }
}

// ---------------------------------------------------------------------------
// Animation Loop (60 FPS) — Pure Zero-Wobble Pulley Wheel Rotation
// ---------------------------------------------------------------------------
const clock = new THREE.Clock();

function animate() {
    requestAnimationFrame(animate);

    const delta = clock.getDelta();
    if (controls && controls.update) {
        controls.update();
    }

    // Rotational Velocity based on Live Telemetry RPM
    const radPerSec = (rpm * 2 * Math.PI) / 60;
    propAngle += radPerSec * delta;
    propGroup.rotation.z = propAngle;

    // PURE ZERO-WOBBLE WHEEL ROTATION (PRE-ROTATED GEOMETRIES AROUND Z)
    crankBlowerPulley.rotation.z = propAngle;            // Crank Blower Pulley
    blowerPulley.rotation.z = propAngle * 1.4;            // Top Blower Snout Pulley
    tensionerPulley.rotation.z = -propAngle * 1.8;         // Side Tensioner Idler

    altPulley.rotation.z = -propAngle * 1.5;
    wpPulley.rotation.z = propAngle * 1.2;
    serptTensioner.rotation.z = -propAngle * 1.8;

    // Smooth Throttle Interpolation for Red Butterfly Valve Plates inside the 3 Bore Holes
    currentButterflyAngle += (targetButterflyAngle - currentButterflyAngle) * 0.1;
    for (let plateGroup of butterflyPlates) {
        plateGroup.rotation.x = currentButterflyAngle;
    }

    // Reciprocating Piston & Connecting Rod V8 Kinematics
    crankAngle += radPerSec * delta;
    const strokeRadius = 0.08;

    for (let i = 0; i < pistons.length; i++) {
        const pObj = pistons[i];
        const rObj = conRods[i];
        const currentCrank = crankAngle + pObj.phase;

        const pistonY = 0.35 + Math.sin(currentCrank) * strokeRadius;
        pObj.mesh.position.y = pistonY;

        const rodTilt = Math.cos(currentCrank) * 0.12;
        rObj.mesh.position.y = pistonY - 0.18;
        rObj.mesh.rotation.z = rodTilt;
    }

    renderer.render(scene, camera);
}
animate();

// Event Listener for Streamlit iframe postMessage
window.addEventListener("message", (event) => {
    updateEngineState(event.data || {});
});

// Direct WebSocket Connection to FastAPI Backend
function connectWebSocket() {
    const wsUrl = (location.protocol === "https:" ? "wss://" : "ws://") + (location.host || "127.0.0.1:8000") + "/ws/telemetry";
    const ws = new WebSocket(wsUrl);

    ws.onmessage = (event) => {
        try {
            const data = JSON.parse(event.data);
            updateEngineState(data);
        } catch (e) {
            // ignore
        }
    };

    ws.onclose = () => {
        setTimeout(connectWebSocket, 2000);
    };

    ws.onerror = () => {
        ws.close();
    };
}
connectWebSocket();

// Responsive Viewport Resize
window.addEventListener("resize", () => {
    camera.aspect = window.innerWidth / window.innerHeight;
    camera.updateProjectionMatrix();
    renderer.setSize(window.innerWidth, window.innerHeight);
});