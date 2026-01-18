#include <Arduino.h>
#include "esp_camera.h"
#include <WiFi.h>
#include <WebServer.h>

// ==================== WiFi Configuration ====================
// Change these to your WiFi credentials (2.4GHz networks only)
const char* ssid = "YOUR_WIFI_SSID";
const char* password = "YOUR_WIFI_PASSWORD";

// ==================== XIAO ESP32S3 Sense Camera Pins ====================
#define PWDN_GPIO_NUM     -1
#define RESET_GPIO_NUM    -1
#define XCLK_GPIO_NUM     10
#define SIOD_GPIO_NUM     40
#define SIOC_GPIO_NUM     39
#define Y9_GPIO_NUM       48
#define Y8_GPIO_NUM       11
#define Y7_GPIO_NUM       12
#define Y6_GPIO_NUM       14
#define Y5_GPIO_NUM       16
#define Y4_GPIO_NUM       18
#define Y3_GPIO_NUM       17
#define Y2_GPIO_NUM       15
#define VSYNC_GPIO_NUM    38
#define HREF_GPIO_NUM     47
#define PCLK_GPIO_NUM     13

// ==================== Web Server ====================
WebServer server(80);

// ==================== HTML Page ====================
const char index_html[] PROGMEM = R"rawliteral(
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>XIAO ESP32S3 Camera</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: #1a1a2e;
            color: #eee;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            padding: 20px;
        }
        h1 {
            margin-bottom: 20px;
            font-weight: 300;
            color: #00d4ff;
        }
        .container {
            background: #16213e;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 8px 32px rgba(0,0,0,0.3);
        }
        #stream {
            border-radius: 8px;
            max-width: 100%;
            display: block;
        }
        .info {
            margin-top: 15px;
            font-size: 14px;
            color: #888;
            text-align: center;
        }
        .status {
            display: inline-block;
            width: 10px;
            height: 10px;
            background: #00ff88;
            border-radius: 50%;
            margin-right: 8px;
            animation: pulse 2s infinite;
        }
        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
        .controls {
            margin-top: 15px;
            display: flex;
            gap: 10px;
            justify-content: center;
            flex-wrap: wrap;
        }
        button {
            background: #0f3460;
            border: none;
            color: #fff;
            padding: 10px 20px;
            border-radius: 6px;
            cursor: pointer;
            font-size: 14px;
            transition: background 0.2s;
        }
        button:hover { background: #00d4ff; color: #000; }
        select {
            background: #0f3460;
            border: none;
            color: #fff;
            padding: 10px 15px;
            border-radius: 6px;
            font-size: 14px;
            cursor: pointer;
        }
    </style>
</head>
<body>
    <h1>XIAO ESP32S3 Camera</h1>
    <div class="container">
        <img id="stream" src="/stream" alt="Camera Stream">
        <div class="info">
            <span class="status"></span>Live Stream - VGA (640x480)
        </div>
        <div class="controls">
            <select id="resolution" onchange="changeResolution()">
                <option value="QVGA">QVGA (320x240)</option>
                <option value="VGA" selected>VGA (640x480)</option>
                <option value="SVGA">SVGA (800x600)</option>
                <option value="XGA">XGA (1024x768)</option>
            </select>
            <select id="quality" onchange="changeQuality()">
                <option value="10">High Quality</option>
                <option value="15" selected>Medium Quality</option>
                <option value="25">Low Quality</option>
            </select>
            <button onclick="capturePhoto()">Capture Photo</button>
        </div>
    </div>
    <script>
        function changeResolution() {
            fetch('/resolution?val=' + document.getElementById('resolution').value);
        }
        function changeQuality() {
            fetch('/quality?val=' + document.getElementById('quality').value);
        }
        function capturePhoto() {
            window.open('/capture', '_blank');
        }
    </script>
</body>
</html>
)rawliteral";

// ==================== Camera Functions ====================
bool initCamera() {
    camera_config_t config;
    config.ledc_channel = LEDC_CHANNEL_0;
    config.ledc_timer = LEDC_TIMER_0;
    config.pin_d0 = Y2_GPIO_NUM;
    config.pin_d1 = Y3_GPIO_NUM;
    config.pin_d2 = Y4_GPIO_NUM;
    config.pin_d3 = Y5_GPIO_NUM;
    config.pin_d4 = Y6_GPIO_NUM;
    config.pin_d5 = Y7_GPIO_NUM;
    config.pin_d6 = Y8_GPIO_NUM;
    config.pin_d7 = Y9_GPIO_NUM;
    config.pin_xclk = XCLK_GPIO_NUM;
    config.pin_pclk = PCLK_GPIO_NUM;
    config.pin_vsync = VSYNC_GPIO_NUM;
    config.pin_href = HREF_GPIO_NUM;
    config.pin_sccb_sda = SIOD_GPIO_NUM;
    config.pin_sccb_scl = SIOC_GPIO_NUM;
    config.pin_pwdn = PWDN_GPIO_NUM;
    config.pin_reset = RESET_GPIO_NUM;
    config.xclk_freq_hz = 20000000;
    config.pixel_format = PIXFORMAT_JPEG;
    config.frame_size = FRAMESIZE_VGA;      // 640x480 (Mark 2 upgrade)
    config.jpeg_quality = 15;               // Balance quality/speed
    config.fb_count = 2;                    // Double buffering for smoother stream
    config.fb_location = CAMERA_FB_IN_PSRAM;
    config.grab_mode = CAMERA_GRAB_LATEST;  // Always get latest frame

    esp_err_t err = esp_camera_init(&config);
    if (err != ESP_OK) {
        Serial.printf("Camera init failed: 0x%x\n", err);
        return false;
    }

    // Optional: Adjust camera settings for better image
    sensor_t *s = esp_camera_sensor_get();
    if (s) {
        s->set_brightness(s, 0);     // -2 to 2
        s->set_contrast(s, 0);       // -2 to 2
        s->set_saturation(s, 0);     // -2 to 2
        s->set_whitebal(s, 1);       // 0 = disable, 1 = enable
        s->set_awb_gain(s, 1);       // 0 = disable, 1 = enable
        s->set_wb_mode(s, 0);        // 0 to 4 - white balance mode
        s->set_aec2(s, 1);           // 0 = disable, 1 = enable
        s->set_gain_ctrl(s, 1);      // 0 = disable, 1 = enable
    }

    return true;
}

// ==================== HTTP Handlers ====================
void handleRoot() {
    server.send_P(200, "text/html", index_html);
}

void handleCapture() {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
        server.send(500, "text/plain", "Camera capture failed");
        return;
    }

    server.sendHeader("Content-Disposition", "inline; filename=capture.jpg");
    server.send_P(200, "image/jpeg", (const char*)fb->buf, fb->len);
    esp_camera_fb_return(fb);
}

void handleStream() {
    WiFiClient client = server.client();

    String response = "HTTP/1.1 200 OK\r\n";
    response += "Content-Type: multipart/x-mixed-replace; boundary=frame\r\n\r\n";
    client.print(response);

    while (client.connected()) {
        camera_fb_t *fb = esp_camera_fb_get();
        if (!fb) {
            Serial.println("Frame capture failed");
            delay(100);
            continue;
        }

        String header = "--frame\r\n";
        header += "Content-Type: image/jpeg\r\n";
        header += "Content-Length: " + String(fb->len) + "\r\n\r\n";

        client.print(header);
        client.write(fb->buf, fb->len);
        client.print("\r\n");

        esp_camera_fb_return(fb);

        // Small delay to control frame rate (~30 fps max)
        delay(33);
    }
}

void handleResolution() {
    if (!server.hasArg("val")) {
        server.send(400, "text/plain", "Missing value");
        return;
    }

    String val = server.arg("val");
    sensor_t *s = esp_camera_sensor_get();

    if (val == "QVGA") s->set_framesize(s, FRAMESIZE_QVGA);
    else if (val == "VGA") s->set_framesize(s, FRAMESIZE_VGA);
    else if (val == "SVGA") s->set_framesize(s, FRAMESIZE_SVGA);
    else if (val == "XGA") s->set_framesize(s, FRAMESIZE_XGA);

    server.send(200, "text/plain", "OK");
}

void handleQuality() {
    if (!server.hasArg("val")) {
        server.send(400, "text/plain", "Missing value");
        return;
    }

    int val = server.arg("val").toInt();
    sensor_t *s = esp_camera_sensor_get();
    s->set_quality(s, val);

    server.send(200, "text/plain", "OK");
}

void handleNotFound() {
    server.send(404, "text/plain", "Not Found");
}

// ==================== Serial Streaming ====================
void sendFrameSerial() {
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
        return;
    }

    // Send frame with markers: FRAME:<size>\n<data>END\n
    Serial.print("FRAME:");
    Serial.println(fb->len);
    Serial.write(fb->buf, fb->len);
    Serial.println("END");

    esp_camera_fb_return(fb);
}

// ==================== Setup ====================
void setup() {
    Serial.begin(921600);  // Higher baud rate for serial streaming
    delay(1000);
    Serial.println("\n\n=== XIAO ESP32S3 Camera - Mark 2 ===");

    // Initialize camera
    Serial.print("Initializing camera... ");
    if (!initCamera()) {
        Serial.println("FAILED!");
        return;
    }
    Serial.println("OK");

    // Connect to WiFi
    Serial.printf("Connecting to WiFi '%s'", ssid);
    WiFi.begin(ssid, password);
    WiFi.setSleep(false);  // Disable WiFi sleep for better streaming

    int attempts = 0;
    while (WiFi.status() != WL_CONNECTED && attempts < 30) {
        delay(500);
        Serial.print(".");
        attempts++;
    }

    if (WiFi.status() != WL_CONNECTED) {
        Serial.println("\nWiFi connection FAILED!");
        Serial.println("Check your SSID and password in the code.");
        return;
    }

    Serial.println(" Connected!");
    Serial.print("IP Address: ");
    Serial.println(WiFi.localIP());

    // Setup web server routes
    server.on("/", handleRoot);
    server.on("/capture", handleCapture);
    server.on("/stream", handleStream);
    server.on("/resolution", handleResolution);
    server.on("/quality", handleQuality);
    server.onNotFound(handleNotFound);

    server.begin();
    Serial.println("\n========================================");
    Serial.println("Camera ready! Open in browser:");
    Serial.print("http://");
    Serial.println(WiFi.localIP());
    Serial.println("========================================\n");
    Serial.println("CAMERA_READY");  // Signal for serial viewer
}

// ==================== Main Loop ====================
unsigned long lastPrint = 0;
bool serialStreamEnabled = true;  // Enable serial streaming by default

void loop() {
    server.handleClient();

    // Send frame over serial (USB) for serial_viewer.py
    if (serialStreamEnabled) {
        sendFrameSerial();
    }

    // Print IP every 30 seconds (less frequent to not interfere with serial stream)
    if (millis() - lastPrint > 30000) {
        // Only print if WiFi connected
        if (WiFi.status() == WL_CONNECTED) {
            Serial.print("IP:");
            Serial.println(WiFi.localIP());
        }
        lastPrint = millis();
    }

    delay(33);  // ~30 fps target
}
