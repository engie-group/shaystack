# Difference between hszinc and shift-4-haystack

At this time (2021/1/1), here are the differences.

| Feature                        | hszinc | shift-4-haystack |
| ------------------------------ |:---:|:---:|
| Parse zinc                     |  Y  |  Y  |
| Parse trio                     |     |  Y  |
| Parse json                     |  Y  |  Y  |
| Parse csv                      |     |  Y  |
| Parse multiple grid            |  Y  |  N  |
| Haystack V2                    |  Y  |  Y  |
| Haystack V3                    |  Y  |  Y  |
| Filter                         |  Y  |  Y  |
| Compare Grid                   |     |  Y  |
| Merge Grid                     |     |  Y  |
| Index entity with 'id'         |     |  Y  |
| Range return grid              |     |  Y  |
| Optimize memory footprint      |     |  Y  |
| Optimize list of columns       |     |  Y  |
| Auto update list of columns    |     |  Y  |
| Convert file type to mode      |     |  Y  |
| Convert mode to file type      |     |  Y  |
| Haystack HTTP API              |     |  Y  |
| Haystack GraphQL API           |     |  Y  |
| Default haystack version       | 2.0 | 3.0 |
| Use pint.Quantity              |     |  Y  |
| Check type of 'id'             |     |  Y  |
| Python                         | 2+  | 3.7+|
| Typing                         |     |  Y  |

To port a code from `hszinc` to `shaystack`:

|  hszinc                       | shift-4-haystack              |
| ----------------------------- | ----------------------------- |
| `import hszinc`               | `import shaystack`            |
| `Grid()`                      | `Grid(version=VER_2_0)`       |
| `g[0]["not"]==None`           | `"not" in g[0]`               |
| `g.append({"id":"@abc"})`     | `g.append({"id":Ref("abc")}`  |
| `Quantity(1,'kg').value`      | `Quantity(1,'kg').m`          |
| `Ref('abc','an entity',True)` | `Ref('abc','an entity')`      |
