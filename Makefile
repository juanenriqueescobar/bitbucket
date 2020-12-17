
test:
	rm -rf tests/output
	ansible-test integration --coverage
	ansible-test coverage html

sanity:
	ansible-test sanity

build: sanity test
	rm *.tar.gz
	ansible-galaxy collection build

publish:
		ansible-galaxy \
		collection publish \
		--token $(TOKEN)\
		*.tar.gz
