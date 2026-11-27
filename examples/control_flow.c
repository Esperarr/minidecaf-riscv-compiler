int main() {
    int sum = 0;
    int i;

    for (i = 0; i < 10; i = i + 1) {
        if (i == 5) {
            continue;
        }
        sum = sum + i;
    }

    return sum > 0 ? sum : 0;
}
