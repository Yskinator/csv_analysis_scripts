
@test "output hasn't changed since last run" {
    rm -f row_to_row_10.csv
    python3 row_to_row_matcher.py many_sites_10.csv -o row_to_row_10.csv >/dev/null
    run diff -q "row_to_row_regression_10.csv" "row_to_row_10.csv"
    [ "$output" = "" ]
}

@test "output (1000 rows) hasn't changed since last run" {
    rm -f row_to_row_1000.csv
    python3 row_to_row_matcher.py many_sites_1000.csv -o row_to_row_1000.csv >/dev/null
    run diff -q "row_to_row_regression_1000.csv" "row_to_row_1000.csv"
    [ "$output" = "" ]
}
