<component name="ProjectRunConfigurationManager">
    <configuration default="false" name="Dockerfile" type="docker-deploy" factoryName="dockerfile" server-name="Docker">
        <deployment type="dockerfile">
            <settings>
                <option name="imageTag" value="engie-group/shaystack"/>
                <option name="buildCliOptions"
                        value="--build-arg PORT=3000 --build-arg REFRESH=1 --build-arg STAGE=dev --build-arg PIP_INDEX_URL=https://test.pypi.org/simple --build-arg HAYSTACK_TS --build-arg PIP_EXTRA_INDEX_URL=https://pypi.org/simple --build-arg HAYSTACK_DB=sample/carytown.json --build-arg HAYSTACK_PROVIDER=shaystack.provider.db"/>
                <option name="command" value=""/>
                <option name="containerName" value="shaystack"/>
                <option name="contextFolderPath" value="."/>
                <option name="entrypoint" value=""/>
                <option name="portBindings">
                    <list>
                        <DockerPortBindingImpl>
                            <option name="containerPort" value="3000"/>
                            <option name="hostPort" value="3000"/>
                        </DockerPortBindingImpl>
                    </list>
                </option>
                <option name="commandLineOptions" value=""/>
                <option name="sourceFilePath" value="docker/Dockerfile"/>
            </settings>
        </deployment>
        <method v="2"/>
    </configuration>
</component>