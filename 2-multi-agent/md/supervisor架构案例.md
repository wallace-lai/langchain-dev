# Supervisor架构多Agent开发案例

## 1. 目标

Supervisor架构示意图如下：

```mermaid
flowchart TD
    User([User])
    Supervisor([Supervisor])
    Agent-1([Agent-1])
    Agent-2([Agent-2])
    Agent-3([Agent-3])

    User --> Supervisor
    Supervisor --> User
    Supervisor -. route .-> Agent-1
    Supervisor -. route .-> Agent-2
    Supervisor -. route .-> Agent-3
    Agent-3 --> Supervisor
    Agent-2 --> Supervisor
    Agent-1 --> Supervisor
```

案例目标：

1. Build a supervisor system with two agents:

- a research expert

- a math expert

2. Build specialized research and math agents

3. Build a supervisor for orchestrating them with the prebuild `langgraph-supervisor`.

4. Build a supervisor from scratch

5. Implement advanced task delegation

## 2. 实现

