import os
import shutil
import sys
import tarfile


def include_package(envoy_api_protos, rst_file_path, prefix):
    # `envoy_api_rst_files` is a list of file paths for .proto.rst files
    # generated by protodoc
    #
    # we are only interested in the proto files generated for envoy protos,
    # not for non-envoy dependencies
    if ("pkg/" + prefix) not in rst_file_path:
        return None
    # derive the "canonical" path from the filepath
    canonical = f"{rst_file_path.split('pkg/' + prefix)[1]}"

    # we are only interested in the actual v3 protos, not their dependencies
    if (prefix + canonical) not in envoy_api_protos:
        return None

    return canonical


def main():
    proto_srcs = sys.argv[1]
    envoy_api_rst_files = sys.argv[1:-1]
    output_filename = sys.argv[-1]

    with open(proto_srcs) as f:
        # the contents of `proto_srcs` are the result of a bazel genquery,
        # containing bazel target rules, eg:
        #
        #   @envoy_api//envoy/watchdog/v3:abort_action.proto
        #
        # this transforms them to a list with a "canonical" form of:
        #
        #   envoy/watchdog/v3/abort_action.proto.rst
        #
        envoy_api_protos = [
            f"{src.split('//')[1].replace(':', '/')}.rst" for src in f.read().split("\n") if src
        ]

    for rst_file_path in envoy_api_rst_files:
        canonical = include_package(envoy_api_protos, rst_file_path, "envoy/")
        if canonical is None:
            canonical = include_package(envoy_api_protos, rst_file_path, "contrib/envoy/")
        if canonical is None:
            continue

        target = os.path.join("rst-out/api-v3", canonical)
        if not os.path.exists(os.path.dirname(target)):
            os.makedirs(os.path.dirname(target))
        shutil.copy(rst_file_path, target)

    # output the generated rst files to a tarfile for consumption
    # by other bazel rules
    with tarfile.open(output_filename, "w") as tar:
        tar.add("rst-out", arcname=".")


if __name__ == "__main__":
    main()
