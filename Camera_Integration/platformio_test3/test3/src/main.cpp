#include <Arduino.h>
#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>
#include <esp_camera.h>

// Replace with your WiFi credentials
// const char* ssid = "Zen Haven 7";
// const char* password = "Peaceful!";

const char* ssid = "The Bruh Phone";
const char* password = "xy1c3m2n";

// Camera pins for Seeed Xiao ESP32S3 (adjust if needed)
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

AsyncWebServer server(80);

void setup() {
  Serial.begin(115200);

  // Connect to WiFi
  WiFi.begin(ssid, password);
  while (WiFi.status() != WL_CONNECTED) {
    delay(1000);
    Serial.println("Connecting to WiFi...");
  }
  Serial.println("Connected to WiFi");
  Serial.print("IP Address: ");
  Serial.println(WiFi.localIP());

  // Camera config
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
  config.frame_size = FRAMESIZE_QVGA;
  config.jpeg_quality = 10;
  config.fb_count = 1;

  // Init camera
  esp_err_t err = esp_camera_init(&config);
  if (err != ESP_OK) {
    Serial.printf("Camera init failed with error 0x%x", err);
    return;
  }
  Serial.println("Camera initialized successfully");

  // Web server routes
  server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
    String html = "<html><head><title>ESP32 Camera Stream</title></head><body>";
    html += "<h1>ESP32 Camera Stream</h1>";
    html += "<img src='/stream' style='width:100%; max-width:640px;'>";
    html += "<br><a href='/capture'>Capture Single Frame</a>";
    html += "</body></html>";
    request->send(200, "text/html", html);
  });

  server.on("/stream", HTTP_GET, [](AsyncWebServerRequest *request){
    AsyncResponseStream *response = request->beginResponseStream("multipart/x-mixed-replace; boundary=frame");
    response->addHeader("Access-Control-Allow-Origin", "*");
    Serial.println("MJPEG stream requested");

    // MJPEG stream
    while (true) {
      camera_fb_t *fb = esp_camera_fb_get();
      if (!fb) {
        Serial.println("Camera capture failed");
        break;
      }

      response->printf("--frame\r\n");
      response->printf("Content-Type: image/jpeg\r\n");
      response->printf("Content-Length: %u\r\n\r\n", fb->len);
      response->write(fb->buf, fb->len);
      response->printf("\r\n");

      esp_camera_fb_return(fb);

      delay(100); // Adjust frame rate
    }

    request->send(response);
  });

  server.on("/capture", HTTP_GET, [](AsyncWebServerRequest *request){
    camera_fb_t *fb = esp_camera_fb_get();
    if (!fb) {
      request->send(500, "text/plain", "Camera capture failed");
      return;
    }
    request->send_P(200, "image/jpeg", (const uint8_t*)fb->buf, fb->len);
    esp_camera_fb_return(fb);
  });

  server.begin();
}

void loop() {
  // Check for serial input to test connection
  if (Serial.available() > 0) {
    char incoming = Serial.read();
    Serial.print("Received: ");
    Serial.println(incoming);
    Serial.println("Connection OK!");
  }
}

// To stream and record using VLC, use the following command:
// vlc http://172.20.10.14/stream --sout=file/mp4:output.mp4 --run-time=30 vlc://quit
