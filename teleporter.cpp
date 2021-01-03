#include <bits/stdc++.h>

using namespace std;

const int MOD = 1<<15;
map<tuple<int, int>, int> dp;
int param;

int ack(int a, int b) {
    a %= MOD;
    b %= MOD;
    if (!a) return (b+1)%MOD;
    tuple<int, int> key = make_tuple(a, b);
    if (dp.count(key)) return dp[key];
    
    if (!b) return dp[key] = ack(a - 1, param);
    else return dp[key] = ack(a - 1, ack(a, b - 1));
}

int ackermann(int k) {
    param = k;
    dp.clear();
    return ack(4, 1);
}

int main() {
    for (int i = 1; i < MOD; i++) {
        if (i%500==0) cout << i << "\n";
        if (ackermann(i) == 6) {
            // RESULT: 25734
            cout << "RESULT: " << i << endl;
            break;
        }
    }
    return 0;
}