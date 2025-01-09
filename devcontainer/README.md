# Devcontiner for Otel Pipelines

This came from building custom collectors, tweak rules in collector configurations, and do all sorts of stuff to Refinery.

This is improving on the `otel-playground` which was fine for yaml engineering but when it's Go time, this is way better.

## What's in the box?

Take this folder and put all of the contents into your workspace's .devcontainer folder. 

I've used this with VS Code on MacOS with Docker so I know it works under those conditions.

### Containers

1. firstcol is an otel collector image
2. refinery1 is a refinery image
3. workspace is a go development environment that can be used to build run refinery or collectors from source

Since this is docker compose defined, you could add stuff from the otel demo or other apps or backends.

### SSH/GitHub

For the git commits to make sense, you need to run:

```shell
git config --file ~/.gitconfig.local user.name "Mike Terhar"
git config --file ~/.gitconfig.local user.email "mike@terhar.com"
```

And if you want to get credit for the commits, you may want to change the values.

I just throw my dotfiles at the new container by doing `curl -SsL https://mjt.sh | sh` 

If you've run `ssh-add` in your local machine terminal, it'll have GitHub access via the SSH agent. 

## Dev Container capabilities

From the dev container json, you can see that it has a docker and vim plugin and runs a `postCreateCommand.sh`.
The `postCreateCommand.sh` installs Delve and the Otel Collector Builder.
The image it's based on is specified in the `docker-compose.yml` file `mcr.microsoft.com/devcontainers/go:1.23-bookworm`.
It seems to have some good stuff in it but I honestly have no idea if it's a good image beyond being able to do what I was doing.

I mainly run:

* Go [build, mod, run, etc]
* curl
* vim for some reason even though there's like a whole text editor thing going on
* docker

All of those commands work great.

## Volumes and configs

There are 2 directories in here, one for the `firstcol` collector config and one for the `refinery1` config and rules files. 
Feel free to change the inputs and outputs and sampling and transforms. 

Most of the config changes I did while working on things were automatically picked up. 
I was recompiling the collector I was building but any changes to the inbound and outbound sides were picked up without restarting.

If you have to restart, you can just use `docker stop` and `docker start` to get them to reload parts of the config that aren't hot-loadable.

### Changing the devcontainer or docker compose configurations

If you want to change an image to a newer one, edit the docker compose files and a little box will pop up in the corner to ask you to rebuild.
If it doesn't pop up, go to "close window" and after about 20 seconds of refinery delaying dying, all the containers will stop. 
When you bring it back up it should ask about rebuilding. 

If you want to connect VS Code to a different container but keep the proper dev container running, just add a new one and set `service` to the new dev container's name. 

## How to run end-to-end tests? 

Loadgen is good.

### Replaying Otel from S3 with Curl

From inside your IDE's devcontainer terminal, you can run curl and reference the first collector by docker's internal DNS.

```shell
curl -X POST http://firstcol:4318/v1/traces -d @otlp_trace.json -H "CONTENT-TYPE: application/json" -H "x-honeycomb-team: hcaik_xxxxxxxxxxxxxxxxxxxxxx"
```

## Sending spans does what?

Firstcol gets it on port 4318. Note that's the internal port rather than the one docker compose exposes to the host.

It then is processed there and logs fall out into docker's std-out. To see them, you can run `docker ps` and get the container IDs.

```shell
docker logs otel-collector-dev_devcontainer-firstcol-1 -f
```

You can do the same to refinery, but I usually send those logs off to Honeycomb. 

```shell
docker logs otel-collector-dev_devcontainer-refinery1-1 -f
```

And because those images are scratch images, you can't shell into them or do anything helpful. 
If they get bad, you're just going to have to start the whole dev environment up again. 
Which should be painless!!!

If you want to see what is happening inside the app you're using, Delve can get you some cool insights and break points.

Make a `.vscode/launch.json` file and put this in it.

```json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Connect to server",
            "type": "go",
            "request": "attach",
            "mode": "remote",
            "port": 2345,
            "host": "127.0.0.1",
            "apiVersion": 2,
            "showLog": true
        }
    ]
}
```

## Downsides

1. If you run an awesome command and want to use it later, save it into a readme or something. History is fleeting.
2. When you do a big rebuild, it has to re-download all the go modules and such. An additional mount could probably solve this but it may make my host machine messier and that's the opposite of the goal here. 