
'''
cd ~/repos/verteilte_systeme/java_rpc/java_grpc
wget -O protoc-gen-grpc-java https://repo1.maven.org/maven2/io/grpc/protoc-gen-grpc-java/1.68.1/protoc-gen-grpc-java-1.68.1-linux-x86_64.exe
chmod +x protoc-gen-grpc-java
'''

'''
protoc \
  --proto_path=app/src/main/resources \
  --plugin=protoc-gen-grpc-java=./protoc-gen-grpc-java \
  --java_out=app/src/main/java \
  --grpc-java_out=app/src/main/java \
  app/src/main/resources/service.proto
'''