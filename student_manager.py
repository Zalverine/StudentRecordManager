from itertools import islice
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation


class Node:
    def __init__(self, roll, name, marks):
        self.roll, self.name, self.marks, self.next = roll, name, marks, None


class StudentList:
    def __init__(self):
        self.head, self.order = None, None  # order: None | "roll" | "marks"

    def __iter__(self):
        cur = self.head
        while cur:
            yield cur
            cur = cur.next

    def add(self, roll, name, marks):
        if not 0 <= marks <= 100:
            raise ValueError("Marks must be between 0 and 100")
        if any(s.roll == roll for s in self):
            raise ValueError(f"Roll {roll} already exists")
        node = Node(roll, name, marks)
        if self.head:
            *_, last = self
            last.next = node
        else:
            self.head = node
        self.order = None

    def delete(self, roll):
        prev, cur = None, self.head
        while cur and cur.roll != roll:
            prev, cur = cur, cur.next
        if not cur:
            return False
        if prev:
            prev.next = cur.next
        else:
            self.head = cur.next
        return True

    def sort(self, field, on_step=None):
        """In-place merge sort: roll ascending, marks descending (stable).
        on_step(nodes, highlights, msg) is called at every comparison for visualisation."""
        before = (lambda a, b: a.roll <= b.roll) if field == "roll" else (lambda a, b: a.marks >= b.marks)
        view = list(self)  # visual order of nodes, kept in sync as sublists get merged

        def chain(n):
            while n:
                yield n
                n = n.next

        def merge(a, b, lo):
            dummy = tail = Node(None, None, None)
            done = []
            while a and b:
                if on_step:
                    rest_a = list(chain(a))
                    seg = done + rest_a + list(chain(b))
                    view[lo:lo + len(seg)] = seg
                    i, j = lo + len(done), lo + len(done) + len(rest_a)
                    hl = {k: "done" for k in range(lo, i)} | {i: "compare", j: "compare"}
                    on_step(view, hl, f"Merge: {a.name} ({getattr(a, field):g}) vs {b.name} ({getattr(b, field):g})")
                if before(a, b):
                    tail.next, a = a, a.next
                else:
                    tail.next, b = b, b.next
                tail = tail.next
                done.append(tail)
            tail.next = a or b
            merged = list(chain(dummy.next))
            view[lo:lo + len(merged)] = merged
            return dummy.next

        def msort(h, lo):
            if not h or not h.next:
                return h
            slow, fast, n = h, h.next, 1  # n = size of left half
            while fast and fast.next:
                slow, fast, n = slow.next, fast.next.next, n + 1
            mid, slow.next = slow.next, None
            return merge(msort(h, lo), msort(mid, lo + n), lo)

        self.head, self.order = msort(self.head, 0), field
        if on_step:
            on_step(view, {k: "done" for k in range(len(view))}, f"Sorted by {field}")

    def search(self, roll, on_step=None):
        """Binary search on the linked list itself (sorts by roll first if needed)."""
        if self.order != "roll":
            self.sort("roll", on_step)
        nodes = list(self) if on_step else []
        start, end, lo, hi = self.head, None, 0, len(nodes)  # lo/hi: indices of start/end, for on_step
        while start is not end:
            slow = fast = start
            mid = lo
            while fast is not end and fast.next is not end:
                slow, fast, mid = slow.next, fast.next.next, mid + 1
            if on_step:
                hl = {k: "out" for k in range(len(nodes)) if not lo <= k < hi} | {mid: "compare"}
                on_step(nodes, hl, f"Search {roll}: check middle roll {slow.roll}")
            if slow.roll == roll:
                if on_step:
                    on_step(nodes, {k: "out" for k in range(len(nodes))} | {mid: "found"}, f"Found roll {roll}")
                return slow
            if slow.roll < roll:
                start, lo = slow.next, mid + 1
            else:
                end, hi = slow, mid
        if on_step:
            on_step(nodes, {k: "out" for k in range(len(nodes))}, f"Roll {roll} not found")
        return None

    def show(self):
        if not self.head:
            return print("No records.")
        print(f"{'Roll':<6}{'Name':<15}{'Marks':>6}")
        for s in self:
            print(f"{s.roll:<6}{s.name:<15}{s.marks:>6g}")


def plot_top5(sl):
    sl.sort("marks")
    top = list(islice(sl, 5))
    if not top:
        return print("No records to plot.")
    plt.figure(figsize=(7, 4))
    bars = plt.bar([f"{s.name}\n#{s.roll}" for s in top], [s.marks for s in top], color="steelblue")
    plt.bar_label(bars)
    plt.title("Top 5 Scorers")
    plt.ylabel("Marks")
    plt.ylim(0, 105)
    plt.tight_layout()
    plt.show()


COLORS = {"compare": "darkorange", "done": "seagreen", "found": "limegreen", "out": "lightgray"}


def recorder(frames):
    """on_step callback that snapshots each step into frames."""
    return lambda nodes, hl, msg: frames.append((list(nodes), hl, msg))


def animate(frames, key, title):
    if not frames:
        return
    n = len(frames[0][0])
    vals = [getattr(s, key) for s in frames[0][0]]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(range(n), vals)
    texts = [ax.text(k, 0, "", ha="center", va="bottom") for k in range(n)]
    ax.set_xticks(range(n))
    ax.set_ylabel(key.capitalize())
    ax.set_ylim((0, 105) if key == "marks" else (min(vals) - 2, max(vals) + 1))
    ax.set_title(f"{title}\n ")  # reserve room for the two-line title before tight_layout

    def update(i):
        nodes, hl, msg = frames[i]
        for k, (bar, txt, s) in enumerate(zip(bars, texts, nodes)):
            v = getattr(s, key)
            bar.set_height(v)
            bar.set_color(COLORS.get(hl.get(k), "steelblue"))
            txt.set_position((k, v))
            txt.set_text(f"{v:g}")
        ax.set_xticklabels([f"{s.name}\n#{s.roll}" for s in nodes])
        ax.set_title(f"{title}  (step {i + 1}/{len(frames)})\n{msg}")

    anim = FuncAnimation(fig, update, frames=len(frames), interval=700, repeat=False)  # noqa: F841 (keep alive)
    fig.tight_layout()
    plt.show()


def ask(prompt, cast=str):
    while True:
        try:
            return cast(input(prompt).strip())
        except ValueError:
            print("Invalid input, try again.")


SAMPLE = [(104, "Aarav", 78), (101, "Diya", 92), (108, "Kabir", 65), (103, "Meera", 88),
          (110, "Rohan", 95), (102, "Isha", 71), (107, "Vivaan", 83), (105, "Anaya", 90)]

MENU = """
1. Add student     2. Delete student   3. Display all
4. Sort by marks   5. Sort by roll     6. Search by roll
7. Plot top 5      0. Exit
> """


def main():
    sl = StudentList()
    for rec in SAMPLE:
        sl.add(*rec)
    while (ch := input(MENU).strip()) != "0":
        if ch == "1":
            try:
                sl.add(ask("Roll: ", int), ask("Name: "), ask("Marks: ", float))
                print("Added.")
            except ValueError as e:
                print(e)
        elif ch == "2":
            print("Deleted." if sl.delete(ask("Roll: ", int)) else "Not found.")
        elif ch == "3":
            sl.show()
        elif ch in ("4", "5"):
            field, frames = ("marks" if ch == "4" else "roll"), []
            sl.sort(field, recorder(frames))
            sl.show()
            animate(frames, field, f"Merge sort by {field}")
        elif ch == "6":
            roll, frames = ask("Roll: ", int), []
            s = sl.search(roll, recorder(frames))
            print(f"Found: {s.name} (roll {s.roll}), marks {s.marks:g}" if s else "Not found.")
            animate(frames, "roll", f"Binary search for roll {roll}")
        elif ch == "7":
            plot_top5(sl)
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
