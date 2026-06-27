#include <micro_ros_arduino.h>
#include <rcl/rcl.h>
#include <rclc/rclc.h>
#include <rclc/executor.h>
#include <geometry_msgs/msg/twist.h>
#include <std_msgs/msg/int32.h>

// ===================== CONFIGURATION =====================
// RIGHT MOTOR - BTS7960
#define MOTOR_RIGHT_PWM 15
#define MOTOR_RIGHT_IN1 2
#define MOTOR_RIGHT_IN2 26

// LEFT MOTOR - BTS7960
#define MOTOR_LEFT_PWM 12
#define MOTOR_LEFT_IN1 13
#define MOTOR_LEFT_IN2 33

// Encoder Pins
#define ENCODER_LEFT_A 14
#define ENCODER_LEFT_B 27
#define ENCODER_RIGHT_A 4
#define ENCODER_RIGHT_B 0

// Robot Physical Parameters
#define WHEEL_RADIUS 0.0845
#define WHEEL_BASE 0.56
#define ENCODER_CPR 400.0

// Control Parameters
#define MAX_LINEAR_SPEED 2.5
#define MAX_ANGULAR_SPEED 2.5
#define PUBLISH_RATE 30

// ===================== GLOBAL VARIABLES =====================
volatile long encoder_left_count = 0;
volatile long encoder_right_count = 0;

unsigned long last_cmd_time = 0;
const unsigned long CMD_TIMEOUT = 500;

// Acceleration ramping
float current_left_pwm = 0.0;
float current_right_pwm = 0.0;
float target_left_pwm = 0.0;
float target_right_pwm = 0.0;

const float ACCEL_RATE = 2.0;
const float LEFT_WHEEL_COMPENSATION = 1.03;

// micro-ROS objects
rcl_subscription_t cmd_vel_subscriber;
rcl_publisher_t left_encoder_publisher;
rcl_publisher_t right_encoder_publisher;
geometry_msgs__msg__Twist cmd_vel_msg;
std_msgs__msg__Int32 left_encoder_msg;
std_msgs__msg__Int32 right_encoder_msg;
rclc_executor_t executor;
rclc_support_t support;
rcl_allocator_t allocator;
rcl_node_t node;
rcl_timer_t timer;

// ===================== ENCODER ISRs =====================
void IRAM_ATTR leftEncoderISR() {
  int b = digitalRead(ENCODER_LEFT_B);
  encoder_left_count += (b == HIGH) ? 1 : -1;
}

void IRAM_ATTR rightEncoderISR() {
  int b = digitalRead(ENCODER_RIGHT_B);
  encoder_right_count += (b == HIGH) ? 1 : -1;
}

// ===================== MOTOR CONTROL =====================
inline void setMotorSpeed(bool isLeft, int speed) {
  speed = constrain(speed, -255, 255);
  if (isLeft) {
    digitalWrite(MOTOR_LEFT_IN2, HIGH);
    if (speed > 0) {
      analogWrite(MOTOR_LEFT_PWM, speed);
      analogWrite(MOTOR_LEFT_IN1, 0);
    } else if (speed < 0) {
      analogWrite(MOTOR_LEFT_PWM, 0);
      analogWrite(MOTOR_LEFT_IN1, abs(speed));
    } else {
      analogWrite(MOTOR_LEFT_PWM, 0);
      analogWrite(MOTOR_LEFT_IN1, 0);
    }
  } else {
    digitalWrite(MOTOR_RIGHT_IN2, HIGH);
    if (speed > 0) {
      analogWrite(MOTOR_RIGHT_PWM, speed);
      analogWrite(MOTOR_RIGHT_IN1, 0);
    } else if (speed < 0) {
      analogWrite(MOTOR_RIGHT_PWM, 0);
      analogWrite(MOTOR_RIGHT_IN1, abs(speed));
    } else {
      analogWrite(MOTOR_RIGHT_PWM, 0);
      analogWrite(MOTOR_RIGHT_IN1, 0);
    }
  }
}

void stopMotors() {
  setMotorSpeed(true, 0);
  setMotorSpeed(false, 0);
}

// ===================== CMD_VEL CALLBACK =====================
void cmd_vel_callback(const void *msgin) {
  const geometry_msgs__msg__Twist *msg = (const geometry_msgs__msg__Twist *)msgin;
  last_cmd_time = millis();

  float linear_vel = msg->linear.x;
  float angular_vel = msg->angular.z;

  // Wheel linear velocities (m/s)
  float left_wheel_vel = linear_vel - (angular_vel * WHEEL_BASE / 2.0);
  float right_wheel_vel = linear_vel + (angular_vel * WHEEL_BASE / 2.0);

  // Convert to angular velocity (rad/s)
  float w_left = left_wheel_vel / WHEEL_RADIUS;
  float w_right = right_wheel_vel / WHEEL_RADIUS;

  // ✅ Correct PWM conversion based on max speed mapping
  // Assume max wheel angular velocity ≈ 5.86 rad/s corresponds to 255 PWM
  target_left_pwm = constrain((w_left / 5.86) * 255.0 * LEFT_WHEEL_COMPENSATION, -255, 255);
  target_right_pwm = constrain((w_right / 5.86) * 255.0, -255, 255);

  setMotorSpeed(true, (int)target_left_pwm);
  setMotorSpeed(false, (int)target_right_pwm);
}

// ===================== ENCODER PUBLISHER =====================
void timer_callback(rcl_timer_t *timer, int64_t last_call_time) {
  (void)timer;
  (void)last_call_time;

  left_encoder_msg.data = encoder_left_count;
  right_encoder_msg.data = encoder_right_count;
  rcl_publish(&left_encoder_publisher, &left_encoder_msg, NULL);
  rcl_publish(&right_encoder_publisher, &right_encoder_msg, NULL);
}

// ===================== MICRO-ROS INITIALIZATION =====================
bool init_micro_ros() {
  allocator = rcl_get_default_allocator();

  if (rclc_support_init(&support, 0, NULL, &allocator) != RCL_RET_OK)
    return false;

  if (rclc_node_init_default(&node, "esp32_diff_drive_node", "", &support) != RCL_RET_OK)
    return false;

  // ✅ QoS tuning
  rmw_qos_profile_t qos_profile = rmw_qos_profile_default;
  qos_profile.reliability = RMW_QOS_POLICY_RELIABILITY_BEST_EFFORT;
  qos_profile.durability = RMW_QOS_POLICY_DURABILITY_VOLATILE;
  qos_profile.history = RMW_QOS_POLICY_HISTORY_KEEP_LAST;
  qos_profile.depth = 1;

  // QoS applied here
  rclc_subscription_init(
    &cmd_vel_subscriber,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(geometry_msgs, msg, Twist),
    "/cmd_vel",
    &qos_profile);

  rclc_publisher_init_default(
    &left_encoder_publisher,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32),
    "/left_encoder");

  rclc_publisher_init_default(
    &right_encoder_publisher,
    &node,
    ROSIDL_GET_MSG_TYPE_SUPPORT(std_msgs, msg, Int32),
    "/right_encoder");

  rclc_timer_init_default(&timer, &support, RCL_MS_TO_NS(1000 / PUBLISH_RATE), timer_callback);

  rclc_executor_init(&executor, &support.context, 2, &allocator);
  rclc_executor_add_subscription(&executor, &cmd_vel_subscriber, &cmd_vel_msg, &cmd_vel_callback, ON_NEW_DATA);
  rclc_executor_add_timer(&executor, &timer);

  return true;
}

// ===================== SETUP =====================
void setup() {
  Serial.begin(115200);
  Serial.println("🔌 Booting ESP32 micro-ROS node...");
  //delay(3000);

  set_microros_transports();

  pinMode(MOTOR_LEFT_IN1, OUTPUT);
  pinMode(MOTOR_LEFT_IN2, OUTPUT);
  pinMode(MOTOR_LEFT_PWM, OUTPUT);
  pinMode(MOTOR_RIGHT_IN1, OUTPUT);
  pinMode(MOTOR_RIGHT_IN2, OUTPUT);
  pinMode(MOTOR_RIGHT_PWM, OUTPUT);

  digitalWrite(MOTOR_LEFT_IN2, HIGH);
  digitalWrite(MOTOR_RIGHT_IN2, HIGH);
  stopMotors();

  pinMode(ENCODER_LEFT_A, INPUT_PULLUP);
  pinMode(ENCODER_LEFT_B, INPUT_PULLUP);
  pinMode(ENCODER_RIGHT_A, INPUT_PULLUP);
  pinMode(ENCODER_RIGHT_B, INPUT_PULLUP);

  attachInterrupt(digitalPinToInterrupt(ENCODER_LEFT_A), leftEncoderISR, RISING);
  attachInterrupt(digitalPinToInterrupt(ENCODER_RIGHT_A), rightEncoderISR, RISING);

  Serial.println("🔁 Connecting to micro-ROS agent...");
  while (!init_micro_ros()) {
    Serial.println("⚠️ micro-ROS agent not found. Retrying...");
    delay(2000);
    set_microros_transports();
  }
  Serial.println("✅ micro-ROS connected!");
  last_cmd_time = millis();
}

// ===================== LOOP =====================
void loop() {
  rcl_ret_t ret = rclc_executor_spin_some(&executor, RCL_MS_TO_NS(5));

  if (ret != RCL_RET_OK) {
    Serial.println("⚠️ Lost connection to micro-ROS agent. Reconnecting...");
    stopMotors();
    delay(2000);
    set_microros_transports();
    while (!init_micro_ros()) {
      Serial.println("🔄 Waiting for agent...");
      delay(2000);
    }
    Serial.println("✅ Reconnected to micro-ROS agent.");
  }

  if (millis() - last_cmd_time > CMD_TIMEOUT) {
    target_left_pwm = 0;
    target_right_pwm = 0;
    stopMotors();
  }
}
