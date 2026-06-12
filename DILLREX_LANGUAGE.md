# Dillrex Language

## File Extension

Dillrex programs use `.drx`.

```text
main.drx
```

## Blocks

Dillrex uses `then` and `end` instead of curly braces.

```drx
if age >= 18 then
    print("Allowed")
end
```

## Final Syntax Sheet

```drx
# comment

import "tools.drx"

set x = 10
set name = ask("Name: ")
set nums = [1, 2, 3]
push(nums, 4)

print("Hello")
print(x)
print(nums[0])

if x > 5 then
    print("big")
else
    print("small")
end

loop x < 20 then
    print(x)
    set x = x + 1
end

fn add(a, b) then
    return a + b
end

set total = add(2, 3)
print(total)

if exists("input.txt") then
    set text = read("input.txt")
    write("output.txt", upper(text))
end
```

## Bootstrapping Plan

The first Dillrex runtime is written in Python so the language has something to run on.
The next goal is to write a second interpreter/compiler in `.drx`.

Stages:

1. Python runs `.drx` files.
2. `.drx` tools read source files, split text, and build token lists.
3. `.drx` parser and runner are added under `bootstrap/`.
4. Python only runs/builds the Dillrex-written version.
5. Later, the Dillrex-built Dillrex can build itself.
