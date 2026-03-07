# 行为树：重新实现“移动同时射击”（RemoteMCP 自研 BTService）

## 目标

不复用/不引用项目里现成的 ShooterCore 节点（如 `BTS_Shoot`），在 **RemoteMCP 插件内重新实现**一套“移动同时射击”的行为树方案：

- 自研 `UBTService_RemoteMCP_MoveAndFire`
- 自研黑板 `BB_MoveAndFire_RemoteMCP_*`
- 自研行为树 `BT_MoveAndFire_RemoteMCP_*`

## 核心思路

- 行为树结构：Root → `BTComposite_SimpleParallel`
  - 主分支：`BTTask_MoveTo`（`BlackboardKey = MoveGoal`）
  - 次分支：`BTTask_Wait`（WaitTime=9999）
- “射击”由 **Service Tick** 驱动（与 MoveTo 并行），Service 每次 Tick：
  - 从黑板读取 `TargetActor`（可选）
  - 可选对目标 `SetFocus`
  - 调用 `RemoteMCPFireInterface::RemoteMCP_Fire(TargetActor)`

> 注意：Service 只负责“何时开火”，真正“如何开火”由你的 Pawn/AIController 自己实现接口决定，这样我们不需要引用任何项目内特定武器/能力节点。

## 插件代码（已实现）

- 接口：`Source/RemoteMCP/Public/AI/RemoteMCPFireInterface.h`
  - `RemoteMCP_Fire(AActor* TargetActor)`
- Service：`Source/RemoteMCP/Public/AI/BTService_RemoteMCP_MoveAndFire.h`
  - `TargetActorKey`（BlackboardKeySelector）
  - `bSetFocusOnTarget`
  - Tick 中调用接口

## 生成的资产（示例）

- Blackboard：
  - `/Game/VerifyAI/BB_MoveAndFire_RemoteMCP_20260111_2129.BB_MoveAndFire_RemoteMCP_20260111_2129`
  - Keys：
    - `MoveGoal` (Vector)
    - `TargetActor` (Object)
- BehaviorTree：
  - `/Game/VerifyAI/BT_MoveAndFire_RemoteMCP_20260111_2130.BT_MoveAndFire_RemoteMCP_20260111_2130`
  - 并行节点挂载 Service：
    - `BTService_RemoteMCP_MoveAndFire`（`TargetActorKey = TargetActor`）

## MCP / Python 关键步骤（已验证）

### 1) 创建黑板并写入 KeyType

关键点：UE5.7 的 Python 里 `BlackboardKeyType_Vector` 不是 `unreal.BlackboardKeyType_Vector`，需要用 `load_class('/Script/AIModule.BlackboardKeyType_Vector')` 再 `new_object`。

### 2) 创建行为树并组装图

Root → SimpleParallel，连接 MoveTo/Wait。

### 3) 绑定黑板并保存（重要）

`bt_set_blackboard` 会 `MarkPackageDirty`，但**需要显式保存 BT 资产**，否则下次校验仍可能引用旧 BB。

为此我们在 Bridge 增加了 `op=get_blackboard`，可用于验证 BT 当前绑定的 BB。

## 如何在你的角色里实现“开火”

你需要在你的 Pawn 或 AIController（任意一个）实现 `RemoteMCPFireInterface`：

- Blueprint：实现 `RemoteMCP_Fire` 事件
- C++：实现 `RemoteMCP_Fire_Implementation`

然后在事件里调用你自己的武器/能力系统进行射击即可（这里不会引用任何 ShooterCore 节点）。

