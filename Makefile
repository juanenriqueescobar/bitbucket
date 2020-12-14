
test:
	rm -rf tests/output
	ansible-test integration --coverage
	ansible-test coverage html

sanity:
	ansible-test sanity

build: sanity test
	ansible-galaxy collection build --force

publish:
		ansible-galaxy \
		collection publish \
		--token $(TOKEN)\
		juanenriqueescobar-bitbucket-$(VERSION).tar.gz
