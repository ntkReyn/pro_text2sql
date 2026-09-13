# Analytics engine

Nơi hiện thực pipeline: intent/router, context retrieval, metric resolution, SQL generation, SQL validation, read-only execution, result profiling, insight, visualization và evidence.

Workflow nên có state rõ ràng, giới hạn số lần retry/repair, timeout và điều kiện dừng để tránh vòng lặp vô hạn.
