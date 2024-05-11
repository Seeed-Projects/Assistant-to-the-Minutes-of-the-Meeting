

启动本地大模型服务
```sh
jetson-containers run --name ollama $(autotag ollama)
```


reComputer J4012 with Jetpack 5.1.2
```sh
docker run --runtime nvidia -it --rm --network host --volume /tmp/argus_socket:/tmp/argus_socket --volume /etc/enctune.conf:/etc/enctune.conf --volume /etc/nv_tegra_release:/etc/nv_tegra_release --volume /tmp/nv_jetson_model:/tmp/nv_jetson_model --volume /var/run/dbus:/var/run/dbus --volume /var/run/avahi-daemon/socket:/var/run/avahi-daemon/socket --volume /var/run/docker.sock:/var/run/docker.sock --volume /home/seeed/aa/microservice/LLM/jetson-containers/data:/data --device /dev/snd --device /dev/bus/usb --name ollama dustynv/ollama:r35.4.1
```



```sh
curl http://localhost:11434/api/generate -d '{
  "model": "llama2",
  "prompt": "Why is the sky blue?"
}'
```

