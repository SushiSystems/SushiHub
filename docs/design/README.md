# Design map

One topic, one document. Look a topic up here before writing; extend the document it names.

## Topics

<!-- topics:begin -->
| Topic | State | About |
| --- | --- | --- |
| [GPU_BACKEND_PROVISIONING](GPU_BACKEND_PROVISIONING/README.md) | Open | GPU backend provisioning: one brick per vendor, one branch per operating system. |
| [HUB](HUB/README.md) | Open | The hub: hub in the terminal and on the desktop. |
| [WORKSPACE_DECOUPLING](WORKSPACE_DECOUPLING/README.md) | Open | Decoupling the hub from the SushiStack checkout. |
<!-- topics:end -->

Standalone provisioning, where every module CLI gains `setup`, `doctor`, `link` and `unlink`, is
designed in the SushiCore repository. Its waves are mirrored in
[REMAINING_WORK.md](../backlog/README.md), which is the single backlog.
