
test:
	rm -rf tests/output
	ansible-test integration --coverage
	ansible-test coverage html
