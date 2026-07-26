ARG BASE_IMAGE
FROM ${BASE_IMAGE}

COPY .azure/fabric/deployer/deploy.py /opt/novasteel-fabric/deploy.py
COPY fabric /opt/novasteel-fabric/fabric

ENTRYPOINT ["python", "/opt/novasteel-fabric/deploy.py"]
