#include <dht.h>
#define lightSensor A1
#define humTempSensor A0

dht DHT;
float rawRange = 1024; // 3.3v
float logRange = 5.0; // 3.3v = 10^5 lux
int amplitude = 1;

void setup() {
  // put your setup code here, to run once:
  pinMode(lightSensor, INPUT);
  pinMode(humTempSensor, INPUT);
  analogReference(EXTERNAL);
  Serial.begin(9600);
  delay(500);//Delay to let system boot
}

void loop() {
  if(Serial.available()>0) {
   amplitude =  Serial.readString().toInt();
  }
  DHT.read11(humTempSensor);
  // put your main code here, to run repeatedly:
    Serial.print(DHT.temperature*amplitude);
  Serial.print(",");

  Serial.print(DHT.humidity*amplitude);
  Serial.print(",");

Serial.print(lightSensor*amplitude);

  Serial.println();
  delay(2000);
}

float RawToLux(int raw)
{
  float logLux = raw * logRange / rawRange;
  return pow(10, logLux);
}
