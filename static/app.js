const socket = io();
const canvas = document.getElementById('visualizer');
const ctx = canvas.getContext('2d');
const statusText = document.getElementById('status-text');

let width, height;
let state = 'idle'; // idle, listening, speaking, processing
let audioContext, analyser, dataArray;
let isMicActive = false;
let currentVolume = 0;
let particles = [];

// Resize handling
function resize() {
    width = window.innerWidth;
    height = window.innerHeight;
    canvas.width = width;
    canvas.height = height;
}
window.addEventListener('resize', resize);
resize();

// --- Particle System ---
class Particle {
    constructor() {
        this.reset();
    }

    reset() {
        // Random position inside a unit circle
        const angle = Math.random() * Math.PI * 2;
        const r = Math.sqrt(Math.random()); // Uniform distribution
        this.baseX = Math.cos(angle) * r;
        this.baseY = Math.sin(angle) * r;

        this.size = Math.random() * 2 + 1; // Tiny dots
        this.speed = Math.random() * 0.05 + 0.01;
        this.wobble = Math.random() * Math.PI * 2;
    }

    update(radius) {
        this.wobble += this.speed;

        // Calculate actual position based on current container radius
        // Add some jitter/life
        let rJitter = Math.sin(this.wobble) * 5;

        this.x = width / 2 + (this.baseX * (radius + rJitter));
        this.y = height / 2 + (this.baseY * (radius + rJitter));
    }

    draw() {
        ctx.fillStyle = `rgba(255, 255, 255, 0.8)`;
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fill();
    }
}

// Create swarm
for (let i = 0; i < 400; i++) {
    particles.push(new Particle());
}

// --- Speech Recognition ---
const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
let recognition = null;

if (SpeechRecognition) {
    recognition = new SpeechRecognition();
    recognition.continuous = true;
    recognition.interimResults = false;
    recognition.lang = 'de-DE';

    recognition.onresult = (event) => {
        const transcript = event.results[event.results.length - 1][0].transcript.trim();
        statusText.innerText = "Heard: " + transcript;
        socket.emit('audio_input', { text: transcript });
        state = 'processing';
        setTimeout(() => { if (state === 'processing') state = 'idle'; }, 2000);
    };

    document.body.onclick = () => {
        if (!isMicActive) {
            startAudio();
            try { recognition.start(); } catch (e) { }
            isMicActive = true;
        }
    };
} else {
    alert("Web Speech API not supported.");
}

// --- Audio Logic ---
async function startAudio() {
    try {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        const source = audioContext.createMediaStreamSource(stream);
        analyser = audioContext.createAnalyser();
        analyser.fftSize = 64;
        source.connect(analyser);
        dataArray = new Uint8Array(analyser.frequencyBinCount);
        statusText.innerText = "MIC ACTIVE - SAY 'PIXEL'";
    } catch (err) {
        statusText.innerText = "MIC ACCESS DENIED";
    }
}

function getVolume() {
    if (!analyser) return 0;
    analyser.getByteFrequencyData(dataArray);
    let sum = 0;
    for (let i = 0; i < dataArray.length; i++) { sum += dataArray[i]; }
    return sum / dataArray.length;
}

// --- Render Loop ---
function animate() {
    ctx.clearRect(0, 0, width, height);

    let vol = getVolume();
    currentVolume += (vol - currentVolume) * 0.2;

    // Determine Target Radius for the "Container"
    let targetRadius = 100; // Base

    if (state === 'speaking') {
        targetRadius = 150 + Math.sin(Date.now() / 100) * 20;
    } else if (state === 'processing') {
        targetRadius = 80; // Compact
    }

    // Add Volume influence
    targetRadius += currentVolume * 2;

    // Update & Draw Particles
    particles.forEach(p => {
        p.update(targetRadius);
        p.draw();
    });

    requestAnimationFrame(animate);
}
animate();

// Socket Events
socket.on('connect', () => { console.log("Connected"); });
socket.on('pixel_state', (data) => {
    if (data.state === 'speaking') state = 'speaking';
    else if (data.state === 'idle') state = 'idle';
    if (data.text) statusText.innerText = data.text;
});
socket.on('notification', (data) => {
    if (Notification.permission === 'granted') new Notification("Pixel", { body: data.message });
});
if (Notification.permission === 'default') Notification.requestPermission();
