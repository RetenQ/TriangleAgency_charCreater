这部分文件夹描述了ARC，即异常体，现实关系和职能。

# Anomaly
结构树大致如下（只描述结构，不展开具体文本）：

- 根对象 `{ }`
  - `"低语"`: `Array`（一组异常能力条目）
    - 每个元素: `Object`
      - `"title"`: `String`  （条目名称，如“再说一遍？”）
      - `"description"`: `String`  （能力描述）
      - `"outcomes"`: `Object`  （掷骰结果）
        - `"success"`: `String`   （成功效果）
        - `"specially"`: `String` （特别成功效果）
        - `"failure"`: `String`   （失败效果）
      - `"interactions"`: `Object`  （与角色问题/抉择相关）
        - `"question"`: `String`  （给玩家的提问）
        - `"options"`: `Array`
          - 每个元素: `Object`
            - `"answer"`: `String` （选项文字）
            - `"code"`: `String`   （对应代码，如 T2、P4 等）

  - `"目录"`: `Array`（另一组异常能力条目，结构与“低语”相同）
    - 每个元素: `Object`
      - `"title"`: `String`
      - `"description"`: `String`
      - `"outcomes"`: `Object`
        - `"success"`: `String`
        - `"specially"`: `String`
        - `"failure"`: `String`
      - `"interactions"`: `Object`
        - `"question"`: `String`
        - `"options"`: `Array`
          - 每个元素: `Object`
            - `"answer"`: `String`
            - `"code"`: `String`


# 现实
结构树如下（只描述结构，不展开具体文本内容）：

- 根对象 `{ }`
  - `"看护者"`: `Object`   （一个能力/现实配置）
    - `"类型"`: `Array<String>`  
      - 每个元素：`String`（如“婴儿”“动物”等）
    - `"现实触发器"`: `Array<Object>`
      - 每个元素: `Object`
        - `"title"`: `String`         （触发器名称）
        - `"description"`: `String`   （描述）
        - `"mechanics"`: `String`     （规则/机制说明）
        - `"track"`: `Object`         （一条进度条/轨道）
          - `"name"`: `String`        （条名，如“独立”）
          - `"steps"`: `Array<String>`（阶段，如 ["1","2","3","4","X"]）
    - `"过载解除"`: `Array<Object>`
      - 每个元素: `Object`
        - `"title"`: `String`         （能力名称）
        - `"description"`: `String`   （解除过载的条件/效果）
    - `"入职问题"`: `Object`
      - `"questionnaire"`: `Array<Object>`
        - 每个元素:
          - `"question"`: `String`    （一个入职/角色问题）

  - `"日程过载"`: `Object`   （结构与“看护者”相同）
    - `"类型"`: `Array<String>`
    - `"现实触发器"`: `Array<Object>`
      - 元素结构：`{ "title", "description", "mechanics", "track" }`
        - `"track"`: `{ "name": String, "steps": Array<String> }`
    - `"过载解除"`: `Array<Object>`
      - 元素结构：`{ "title": String, "description": String }`
    - `"入职问题"`: `Object`
      - `"questionnaire"`: `Array<Object>`
        - 元素结构：`{ "question": String }`


# 职能
结构树如下（只描述结构，不展开具体文本内容）：

- 根对象 `{ }`  
  - `"咖啡师"`: `Array`（一组现实配置条目）  
    - 每个元素: `Object`  
      - `"MAIN"`: `String`               （核心原则）  
      - `"MAIN_description"`: `String`   （原则说明）  
      - `"initial_item"`: `Object`       （初始物品）  
        - `"title"`: `String`            （物品名）  
        - `"description"`: `String`      （物品描述）  
      - `"permitted_actions"`: `Object`  （许可行为与奖励）  
        - `"description"`: `String`      （总说明，如“每当你……时，获得 1 次嘉奖：”）  
        - `"list"`: `Array<String>`      （若干许可行为条目）  
        - `"bonus"`: `String`            （额外奖励说明）  
      - `"interactions"`: `Array<Object>`（互动问题与性格选项）  
        - 每个元素: `Object`  
          - `"question"`: `String`       （问题文本）  
          - `"options"`: `Array<Object>`  
            - 每个元素: `Object`  
              - `"answer"`: `String`     （选项文字）  
              - `"code"`: `String`       （对应代码，如“+3 共情”等）  
      - `"quote"`: `String`              （一句引用/格言）  

  - `"公关"`: `Array`（结构与 `"咖啡师"` 相同）  
    - 每个元素: `Object`  
      - `"MAIN"`: `String`  
      - `"MAIN_description"`: `String`  
      - `"initial_item"`: `Object`  
        - `"title"`: `String`  
        - `"description"`: `String`  
      - `"permitted_actions"`: `Object`  
        - `"description"`: `String`  
        - `"list"`: `Array<String>`  
        - `"bonus"`: `String`  
      - `"interactions"`: `Array<Object>`  
        - 每个元素: `Object`  
          - `"question"`: `String`  
          - `"options"`: `Array<Object>`  
            - 每个元素: `Object`  
              - `"answer"`: `String`  
              - `"code"`: `String`  
      - `"quote"`: `String`  

  - 其他顶层键（若有，如其他职能名称）: `Array`  
    - 每个顶层键对应的数组元素结构与 `"咖啡师"` / `"公关"` 相同。