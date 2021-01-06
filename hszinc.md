# Difference between hszinc and haystackapi

At this time (2021/1/1), here are the differences.

| Feature                        | hszinc | haystackapi |
| ------------------------------ |:---:|:---:|
| Parse zinc                     |  Y  |  Y  |
| Parse json                     |  Y  |  Y  |
| Parse csv                      |     |  Y  |
| Filter                         |  Y  |  Y  |
| Compare grid                   |     |  Y  |
| Merge grid                     |     |  Y  |
| Index entity with 'id'         |     |  Y  |
| Range return grid              |     |  Y  |
| Optimize column                |     |  Y  |
| Convert file type to extension |     |  Y  |
| Haystack REST API              |     |  Y  |
| Haystack GraphQL API           |     |  Y  |
| Default haystack version       | 2.0 | 3.0 |
| Use unit with pint             | opt.|  Y  |

To port a code from `hszinc` to `haystackapi`:

|  hszinc         | haystackapi             |
| --------------- | ----------------------- |
| `import hszinc` | `import haystackapi`    |
| `Grid()`        | `Grid(version=VER_2_0)` |
