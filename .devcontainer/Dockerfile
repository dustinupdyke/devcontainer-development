FROM mcr.microsoft.com/devcontainers/dotnet:10.0

ARG TARGETARCH
USER root

# Remove the flotsam around Yarn
RUN rm -f /etc/apt/sources.list.d/yarn.list /etc/apt/sources.list.d/yarn*.list

USER vscode
