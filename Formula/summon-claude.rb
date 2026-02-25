class SummonClaude < Formula
  include Language::Python::Virtualenv

  desc "Bridge Claude Code sessions to Slack channels"
  homepage "https://github.com/wgordon17/summon-claude"
  url "https://files.pythonhosted.org/packages/0a/66/483e2d31ac0e264c73964c0ab5893af616c72c46b5b5b58e7dc8b44b39d6/summon_claude-0.1.0.tar.gz"
  sha256 "79f6e31b809e1b1ee559dc1bc42c0c8033478ee861fbb02c03ec1da554e29950"
  license "MIT"

  depends_on "python@3.13"

  def install
    virtualenv_install_with_resources
  end

  test do
    assert_match "summon, version", shell_output("#{bin}/summon version")
  end
end
